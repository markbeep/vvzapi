from sqlmodel import JSON, Field, Column
from api.new_models.base import BaseModel
from api.new_models.lehrveranstaltungen import Lehrveranstaltung


class Lerneinheit(BaseModel, table=True):
    """WsLerneinheit"""

    id: int = Field(primary_key=True)
    """Technische Identifikation der Lerneinheit. Diese Id ist eindeutig."""
    code: str | None = Field(default=None, max_length=12)
    """Nummer/Code zu dieser Lerneinheit. Eindeutige Identifizierung einer LE innerhalb eines Semesters"""
    titel: str | None = Field(default=None, max_length=100)
    """Titel dieser Lerneinheit."""
    titelenglisch: str | None = Field(default=None, max_length=100)
    """Titel dieser Lerneinheit auf Englisch."""
    semkez: str = Field(max_length=5)
    """
    Identifiziert das Semester, in der die Lerneinheit stattfindet.
    Codierung des Semesters im Format 9999(S|W), wobei 9999 eine vierstellige
    Jahreszahl beschreibt und S für Sommersemester und W für Wintersemester steht.
    Beispiele: 2004S, 2005W.
    """
    kreditpunkte: float | None = Field(default=None)
    """
    Erreichbare Kreditpunkte für diese Lerneinheit.
    Bemerkung-1:
    Wenn die Lerneinheit im Rahmen eines neuen
    Studienganges absolviert wird, definiert dieses Attribut die
    Anzahl der Kreditpunkte, die für die Lerneinheit bei
    erfolgreichem Bestehen der Leistungskontrolle erteilt
    werden.
    Diese Angabe ist verbindlich für alle Absolvenden der
    Lerneinheit, deren Studiengang der 'Allgemeinen Verordung
    über Leistungskontrollen' untersteht (das sind alle neuen,
    gestuften Studiengänge, d.h. Bachelor und Master-
    Studiengänge).
    Bemerkung-2: Wenn die Lerneinheit im Rahmen eines alten
    Diplomstudiengangs absolviert wird, definiert dieses Attribut
    die Anzahl Krediteinheiten die üblicherweise eine Student/in
    bei erreichen der Kreditbedingungen für diese Lerneinheit
    erhält. Dieser Defaultwert kann dann bei der Zuordung
    überschrieben werden. Die effektive Anzahl der
    Krediteinheiten wird pro Student/in vergeben und kann in
    Ausnahmefällen von der "Default"-Krediteinheit abweichen
    """
    url: str | None = Field(default=None, max_length=1000)
    """
    URL für eine spezifische Homepage zu dieser Lerneinheit.
    Enthält weiter Angaben und Beschreibungen zur Vorlesung
    und dem Übungsbetrieb oder Übungsunterlagen.
    Für die Auswertung der URL ist auch der Gültigkeitsbereich
    der URL auszuwerten.
    """
    literatur: str | None = Field(default=None, max_length=4000)
    """Literaturangaben zu dieser Lerneinheit."""
    literaturenglisch: str | None = Field(default=None, max_length=4000)
    """Literaturangaben zu dieser Lerneinheit auf Englisch."""
    lernziel: str | None = Field(default=None, max_length=4000)
    """Lernziele dieser Lerneinheit."""
    lernzielenglisch: str | None = Field(default=None, max_length=4000)
    """Lernziele dieser Lerneinheit auf Englisch."""
    inhalt: str | None = Field(default=None, max_length=4000)
    """Inhaltsbeschreibung dieser Lerneinheit."""
    inhaltenglisch: str | None = Field(default=None, max_length=4000)
    """Inhaltsbeschreibung dieser Lerneinheit auf Englisch."""
    skript: str | None = Field(default=None, max_length=4000)
    """Angaben zum Skrip für diese Lerneinheit."""
    skriptenglisch: str | None = Field(default=None, max_length=4000)
    """Angaben zum Skrip für diese Lerneinheit auf Englisch."""
    besonderes: str | None = Field(default=None, max_length=4000)
    """Besonderes zu dieser Lerneinheit."""
    besonderesenglisch: str | None = Field(default=None, max_length=4000)
    """Besonderes zu dieser Lerneinheit auf Englisch."""
    diplomasupplement: str | None = Field(default=None, max_length=4000)
    """Text für das Diplomasupplement dieser Lerneinheit."""
    diplomasupplementenglisch: str | None = Field(default=None, max_length=4000)
    """Text für das Diplomasupplement dieser Lerneinheit auf Englisch."""
    angezeigterkommentar: str | None = Field(default=None, max_length=1000)
    """
    Im elektronischen Vorlesungsverzeichnis angezeigter
    Kommentar zu dieser Lerneinheit.
    Dieser Kommentar hat keinen direkten Bezug auf den Inhalt
    der Lerneinheit, sondern gibt Zusatzinformationen zu dieser
    Lerneinheit für die Publikation im elektronischen
    Vorlesungsverzeichnis
    """
    angezeigterkommentaren: str | None = Field(default=None, max_length=1000)
    """
    Im elektronischen Vorlesungsverzeichnis angezeigter
    englischer Kommentar zu dieser Lerneinheit.
    Dieser Kommentar hat keinen direkten Bezug auf den Inhalt
    der Lerneinheit, sondern gibt Zusatzinformationen zu dieser
    Lerneinheit für die Publikation im elektronischen
    Vorlesungsverzeichnis.
    """
    sternkollonne: str | None = Field(default=None)
    """
    Die Zusatzinformationen aus dem VVZ. Hier kann auch
    abgelesen werden, ob es sich um eine obligatorische
    Veranstaltung handelt.
    """
    belegungMaxPlatzzahl: int | None = Field(default=None)
    """Anzahl zur Verfügung stehender Plätze (falls definiert, sonst leer)"""
    belegungTermin2Wl: str | None = Field(default=None)
    """
    Bis zu diesem Termin (falls vorhanden, sonst leer) wird eine
    Warteliste geführt. Danach gibt es nur noch definitive
    Belegungen.
    """
    belegungTermin3Ende: str | None = Field(default=None)
    """
    Ab diesem Termin (falls vorhanden, sonst leer) kann die LE
    gar nicht mehr belegt werden.
    Format yyyy-mm-dd
    """
    lehrveranstaltungen: list[Lehrveranstaltung] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    """
    Liste der Lehrveranstaltungen, die zur Lerneinheit gehören.
    Falls für die Lerneinheit keine Lehrveranstaltungen erfasst
    sind, so wird der leere Array zurückgegeben.
    Format yyyy-mm-dd
    """

    # NOTE: Not listed in doc, but listed on vvz
    belegungsTerminStart: str | None = Field(default=None)
    vorrang: str | None = Field(default=None)

    # NOTE: Listed in doc, but removed because not available on vvz or not relevant
    # urlvon: str | None = Field(default=None)
    # urlbis: str | None = Field(default=None)
    # reihenfolge: int | None = Field(default=None)
    # lkeinheitid: int | None = Field(default=None)

    def overwrite_with(self, other: "Lerneinheit"):
        """
        Overwrites all fields that are not None from the other instance.
        Used to merge german and english scraped data.
        """
        for field in other.model_fields_set:
            value = getattr(other, field)
            if value is not None:
                setattr(self, field, value)
