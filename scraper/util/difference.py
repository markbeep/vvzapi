from api.models import LearningUnit, UnitChanges


def find_unit_differences(old: LearningUnit, new: LearningUnit) -> UnitChanges | None:
    if old.id != new.id:
        raise ValueError("Can only compare LearningUnits with the same unit_id")

    diffs = {}
    for field in old.model_fields_set:
        val_old = getattr(old, field)
        val_new = getattr(new, field)
        if val_new is None:
            continue
        if val_old != val_new:
            diffs[field] = val_new

    if not diffs:
        return None

    return UnitChanges(
        unit_id=old.id,
        changes=diffs,
        scraped_at=old.scraped_at,
    )
