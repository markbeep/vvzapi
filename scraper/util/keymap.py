from pydantic import BaseModel
from typing import Literal


class Translation(BaseModel):
    de: str
    en: str


TranslationKey = Literal[
    # root
    "semester",
    "lecturers",
    "periodicity",
    "course",
    "language",
    "comment",
    # Catalogue data
    "abstract",
    "learning_objective",
    "content",
    "notice",
    "competencies",
    "lecture_notes",
    "literature",
    "url",
    # Performance assessment
    "assessment_information",
    "semester_course",
    "two_semester_course",
    "credits",
    "examiners",
    "type",
    "exam_language",
    "repetition",
    "exam_mode",
    "additional_info",
    "digital",
    "admission_requirement",
    "exam_block",
    "written_aids",
    "to_be_updated",
    "regulations",
    "part_of_exam_block",
    "distance_exam",
    # Learning materials
    "no_materials",
    "public_materials",
    "no_group_info",
    # Restrictions
    "places",
    "waiting_list",
    "registration_end",
    "registration_start",
    "priority",
    "primary_target_group",
    "general_restrictions",
    # Groups
    "groups",
    #
    "other",
    "unkeyed",
]

translations: dict[TranslationKey, Translation] = {
    # root
    "semester": Translation(de="Semester", en="Semester"),
    "lecturers": Translation(de="Dozierende", en="Lecturers"),
    "periodicity": Translation(de="Periodizität", en="Periodicity"),
    "course": Translation(de="Lehrveranstaltung", en="Course"),
    "language": Translation(de="Lehrsprache", en="Language of instruction"),
    "comment": Translation(de="Kommentar", en="Comment"),
    "url": Translation(de="Hauptlink", en="Main link"),
    # Catalogue data
    "abstract": Translation(de="Kurzbeschreibung", en="Abstract"),
    "learning_objective": Translation(de="Lernziel", en="Learning objective"),
    "content": Translation(de="Inhalt", en="Content"),
    "notice": Translation(
        de="Voraussetzungen / Besonderes", en="Prerequisites / Notice"
    ),
    "competencies": Translation(de="Kompetenzen", en="Competencies"),
    "lecture_notes": Translation(de="Skript", en="Lecture notes"),
    "literature": Translation(de="Literatur", en="Literature"),
    # Performance assessment
    "assessment_information": Translation(
        de="Information zur Leistungskontrolle (gültig bis die Lerneinheit neu gelesen wird)",
        en="Performance assessment information (valid until the course unit is held again)",
    ),
    "semester_course": Translation(
        de="Leistungskontrolle als Semesterkurs",
        en="Performance assessment as a semester course",
    ),
    "two_semester_course": Translation(
        de="Leistungskontrolle als Jahreskurs",
        en="Performance assessment as a two-semester course",
    ),
    "credits": Translation(de="ECTS Kreditpunkte", en="ECTS credits"),
    "examiners": Translation(de="Prüfende", en="Examiners"),
    "type": Translation(de="Form", en="Type"),
    "exam_language": Translation(de="Prüfungssprache", en="Language of examination"),
    "repetition": Translation(de="Repetition", en="Repetition"),
    "exam_mode": Translation(de="Prüfungsmodus", en="Mode of examination"),
    "additional_info": Translation(
        de="Zusatzinformation zum Prüfungsmodus",
        en="Additional information on mode of examination",
    ),
    "digital": Translation(de="Digitale Prüfung", en="Digital exam"),
    "admission_requirement": Translation(
        de="Zulassungsbedingung", en="Admission requirement"
    ),
    "exam_block": Translation(de="Im Prüfungsblock für", en="In examination block for"),
    "written_aids": Translation(de="Hilfsmittel schriftlich", en="Written aids"),
    "to_be_updated": Translation(
        de="Diese Angaben können noch zu Semesterbeginn aktualisiert werden; verbindlich sind die Angaben auf dem Prüfungsplan.",
        en="This information can be updated until the beginning of the semester; information on the examination timetable is binding.",
    ),
    "regulations": Translation(de="Für Reglement", en="For programme regulations"),
    "part_of_exam_block": Translation(
        de="Falls die Lerneinheit innerhalb eines Prüfungsblockes geprüft wird, werden die Kreditpunkte für den gesamten bestandenen Block erteilt.",
        en="If the course unit is part of an examination block, the credits are allocated for the successful completion of the whole block.",
    ),
    "distance_exam": Translation(de="Fernprüfung", en="Distance examination"),
    # Learning materials
    "no_materials": Translation(
        de="Keine öffentlichen Lernmaterialien verfügbar.",
        en="No public learning materials available.",
    ),
    "public_materials": Translation(
        de="Es werden nur die öffentlichen Lernmaterialien aufgeführt.",
        en="Only public learning materials are listed.",
    ),
    "no_group_info": Translation(
        de="Keine Informationen zu Gruppen vorhanden.",
        en="No information on groups available.",
    ),
    # Restrictions
    "places": Translation(de="Plätze", en="Places"),
    "waiting_list": Translation(de="Warteliste", en="Waiting list"),
    "registration_end": Translation(
        de="Belegungsende", en="End of registration period"
    ),
    "registration_start": Translation(
        de="Belegungsbeginn", en="Beginning of registration period"
    ),
    "priority": Translation(de="Vorrang", en="Priority"),
    "primary_target_group": Translation(
        de="Primäre Zielgruppe", en="Primary target group"
    ),
    "general_restrictions": Translation(de="Allgemein", en="General"),
    # Groups
    "groups": Translation(de="Gruppen", en="Groups"),
}


def get_key(value: str) -> TranslationKey:
    for key, translation in translations.items():
        if value.startswith(translation.de) or value.startswith(translation.en):
            return key
    return "other"
