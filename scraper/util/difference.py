# pyright: reportExplicitAny=false,reportAny=false


from typing import Any, Literal
from api.models import LearningUnit, UnitChanges


def _determine_lang(unit: LearningUnit) -> Literal["en", "de"]:
    """
    Determines if a new unit model is added as an english or german part.
    Defaults to "de" if no English fields are set.
    """
    for field, value in unit:
        if field.endswith("_english") and value is not None:
            return "en"
    return "de"


def _has_language_key(unit: LearningUnit, lang: Literal["en", "de"]):
    """Determines if a model already has keys of a language"""
    for field, value in unit:
        if field.endswith("_english"):
            if lang == "en" and value is not None:
                return True
            elif lang == "de" and getattr(unit, field[:-8]) is not None:
                return True
    return False


def find_unit_differences(old: LearningUnit, new: LearningUnit) -> UnitChanges | None:
    """
    Determines if there are any differences between an already existing model (from the DB)
    and from a newly yielded item. The new item is either an English or German unit, meaning
    either the English or German catalogue data is filled out, while the other language fields
    are None. In a scraping run we'll always get both a "German" and "English" catalogue data
    unit as well as an "English" unit with the additional data.
    By determining the language of a model we avoid the issue where `old` is "English", while
    `new` is "German", so all the English fields are incorrectly identified as having been
    removed because they're not present in the new model anymore.
    """

    if old.id != new.id:
        raise ValueError("Can only compare LearningUnits with the same unit_id")

    new_lang = _determine_lang(new)
    if not _has_language_key(old, new_lang):
        # There are no differences to check, since the old model does not have any language
        # specific values of the same language as the new item.
        return None

    diffs: dict[str, Any] = {}
    # only iterate over explicitly set fields to avoid checking default/None values
    for field in new.model_fields_set:
        val_old = getattr(old, field)
        val_new = getattr(new, field)
        if val_old != val_new:
            diffs[field] = val_old

    if not diffs:
        return None

    return UnitChanges(
        unit_id=old.id,
        changes=diffs,
        scraped_at=old.scraped_at,
    )
