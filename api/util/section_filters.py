from dataclasses import dataclass

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import Section
from api.util.db import aengine


@dataclass(frozen=True)
class SectionOption:
    id: int
    label: str
    path: tuple[str, ...]
    parent_id: int | None
    level: int


@dataclass(frozen=True)
class SectionFilterData:
    latest_semester: str | None
    programmes: tuple[SectionOption, ...]
    sections: tuple[SectionOption, ...]
    selected_programme: SectionOption | None
    selected_section: SectionOption | None

    @property
    def path_names(self) -> tuple[str, ...]:
        if self.selected_section:
            return self.selected_section.path
        if self.selected_programme:
            return self.selected_programme.path
        return ()

    @property
    def active_label(self) -> str | None:
        if self.selected_section:
            return " › ".join(self.selected_section.path)
        if self.selected_programme:
            return self.selected_programme.label
        return None


@dataclass(frozen=True)
class _Info:
    id: int
    parent_id: int | None
    level: int
    name: str


async def get_section_filter_data(
    programme_id: int | None = None,
    section_id: int | None = None,
) -> SectionFilterData:
    async with AsyncSession(aengine) as session:
        latest = await session.scalar(select(func.max(Section.semkez)))
        if not latest:
            return SectionFilterData(None, (), (), None, None)
        section_rows = (
            await session.exec(select(Section).where(col(Section.semkez) == latest))
        ).all()

    info = {
        row.id: _Info(
            id=row.id,
            parent_id=row.parent_id,
            level=row.level or 0,
            name=row.name_english or row.name or "Unnamed section",
        )
        for row in section_rows
    }

    @dataclass(frozen=True)
    class PathInfo:
        names: tuple[str, ...]
        root_id: int

    paths: dict[int, PathInfo] = {}

    def path_of(section: int) -> PathInfo | None:
        cached = paths.get(section)
        if cached:
            return cached
        names: list[str] = []
        current: int | None = section
        seen: set[int] = set()
        root_id: int | None = None
        while current is not None and current in info and current not in seen:
            seen.add(current)
            node = info[current]
            names.append(node.name)
            root_id = current
            current = node.parent_id
        if root_id is None:
            return None
        result = PathInfo(tuple(reversed(names)), root_id)
        paths[section] = result
        return result

    roots: list[SectionOption] = []
    for node in info.values():
        if node.parent_id is None:
            roots.append(
                SectionOption(
                    id=node.id,
                    label=node.name,
                    path=(node.name,),
                    parent_id=None,
                    level=node.level,
                )
            )
    roots.sort(key=lambda option: option.label)

    selected_programme: SectionOption | None = None
    if programme_id is not None:
        selected_programme = next(
            (option for option in roots if option.id == programme_id), None
        )

    selected_section: SectionOption | None = None
    if section_id is not None and section_id in info:
        selected_path = path_of(section_id)
        if selected_path and selected_path.root_id != section_id:
            selected_section = SectionOption(
                id=section_id,
                label=" › ".join(selected_path.names[1:]),
                path=selected_path.names,
                parent_id=info[section_id].parent_id,
                level=info[section_id].level,
            )

    if selected_section:
        root_id = path_of(selected_section.id)
        if root_id:
            selected_programme = next(
                (option for option in roots if option.id == root_id.root_id),
                None,
            )

    section_options: list[SectionOption] = []
    if selected_programme:
        for node in info.values():
            if node.id == selected_programme.id:
                continue
            path = path_of(node.id)
            if not path or path.root_id != selected_programme.id:
                continue
            section_options.append(
                SectionOption(
                    id=node.id,
                    label=" › ".join(path.names[1:]),
                    path=path.names,
                    parent_id=node.parent_id,
                    level=node.level,
                )
            )
        section_options.sort(key=lambda option: option.label)

    if (
        selected_programme
        and selected_section
        and selected_section.id not in {option.id for option in section_options}
    ):
        selected_section = None

    return SectionFilterData(
        latest_semester=latest,
        programmes=tuple(roots),
        sections=tuple(section_options),
        selected_programme=selected_programme,
        selected_section=selected_section,
    )
