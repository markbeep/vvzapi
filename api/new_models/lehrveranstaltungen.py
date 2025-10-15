from sqlmodel import JSON, Column, Field
from api.new_models.base import BaseModel
from api.new_models.belegungsserie_ort import BelegungsserieOrt
from api.new_models.lehrveranstalter import Lehrveranstalter


class Lehrveranstaltung(BaseModel, table=True):
    """WsLehrveranstaltung"""

    id: int = Field(primary_key=True)
    """Technische Identifikation dieser Lehrveranstaltung"""
    nummer: str | None = Field(default=None)
    """Nummer der Lehrveranstaltung"""
    titel: str | None = Field(default=None)
    """Bezeichnung der Lehrveranstaltung (ohne englische Übersetzung)"""
    semkez: str | None = Field(default=None, max_length=5)
    """
    Identifiziert das Semester, in der die Lehrveranstaltung stattfindet.
    Codierung des Semesters im Format 9999(S|W), wobei
    9999 eine vierstellige Jahreszahl beschreibt und S für
    Sommersemester und W für Wintersemester steht.
    Beispiele: 2004S, 2005W.
    """
    typ: str | None = Field(default=None, max_length=1)
    """
    Typ der Lehrveranstaltung. Die folgenden Werte sind möglich:
    - A selbstständige Arbeit
    - D Diplomarbeit
    - G Vorlesung mit Uebung
    - K Kolloquium
    - P Praktikum
    - R Repetitorium
    - S Seminar
    - U Uebung
    - V Vorlesung
    """
    semesterbezug: int | None = Field(default=None)
    """
    Numerischer Wert, der den Bezug der Lehrveranstaltung zum Semester beschreibt:
    - 0 kein Semesterbezug (kein)
    - 1 ganzes Semester (ganz)
    - 2 nur in der 1. Semesterhälfte (1. Hälfte)
    - 3 nur in der 2. Semesterhälfte (2. Hälfte)
    """
    semesterbezugstringkurz: str | None = Field(default=None)
    """Kurze Bezeichnung für den Bezug der Lehrveranstaltung zum Semester beschreibt."""
    semesterbezugstringkurzen: str | None = Field(default=None)
    """Kurze englische Bezeichnung für den Bezug der Lehrveranstaltung zum Semester beschreibt."""
    semesterbezugstringlang: str | None = Field(default=None)
    """Lange Bezeichnung für den Bezug der Lehrveranstaltung zum Semester beschreibt."""
    semesterbezugstringlangen: str | None = Field(default=None)
    """Lange englische Bezeichnung für den Bezug der Lehrveranstaltung zum Semester beschreibt."""
    lehrumfang: float | None = Field(default=None, max_digits=7, decimal_places=2)
    """
    Angabe der Anzahl Stunden des Lehrumfangs dieser
    Lehrveranstaltung. Lehrumfang in Wochen- oder
    Semesterstunden, abhängig von Lehrumfangtyp.:
    Fünf Vorkommastellen und zwei Nachkommastellen.
    """
    lehrumfangtyp: int | None = Field(default=None)
    """
    Beschreibt, wie sich die Angabe im Attribut lehrumfang zu verstehen ist.
    Definiert Masseinheit für Lehrumfang (zB "Wochenstunden" oder "Semesterstunden"):
    - 1 Wochenstunden (Wochenstd.)
    - 2 Semesterstunden (Sem.Std.)
    """
    lehrumfangtypstringkurz: str | None = Field(default=None)
    """Kurze Bezeichnung, wie sich die Angabe im Attribut lehrumfang zu verstehen ist:"""
    lehrumfangtypstringkurzen: str | None = Field(default=None)
    """Kurze englische Bezeichnung, wie sich die Angabe im Attribut lehrumfang zu verstehen ist:"""
    lehrumfangtypstringlang: str | None = Field(default=None)
    """Lange Bezeichnung, wie sich die Angabe im Attribut lehrumfang zu verstehen ist:"""
    lehrumfangtypstringlangen: str | None = Field(default=None)
    """Lange englische Bezeichnung, wie sich die Angabe im Attribut lehrumfang zu verstehen ist:"""
    findetstatt: int | None = Field(default=None)
    """
    Flag, ob diese Veranstaltung stattfindet oder nicht.
    - 0 Veranstaltung findet dieses Jahr nicht statt (nein)
    - 1 Veranstaltung findet dieses Jahr statt (ja)
    - 2 Annuliert (Annuliert)
    """
    findetstattstringkurz: str | None = Field(default=None)
    """Kurze Bezeichnung, ob diese Veranstaltung stattfindet oder nicht."""
    findetstattstringkurzen: str | None = Field(default=None)
    """Kurze englische Bezeichnung, ob diese Veranstaltung stattfindet oder nicht."""
    findetstattstringlang: str | None = Field(default=None)
    """Lange Bezeichnung, ob diese Veranstaltung stattfindet oder nicht."""
    findetstattstringlangen: str | None = Field(default=None)
    """Lange englische Bezeichnung, ob diese Veranstaltung stattfindet oder nicht."""
    servicetyp: int | None = Field(default=None)
    """
    Servicetyp für diese Lehrveranstaltung.
    - 0 Keine Service-Veranstaltung (keine SV)
    - 1 Service-Veranstaltung für obligatorische LV (oblig. LV)
    - 2 Service-Veranstaltung für fakulatative LV (fakult. LV)
    """
    servicetypstringkurz: str | None = Field(default=None)
    """Kurze Bezeichnung der Servicetyp dieser Lehrveranstaltung."""
    servicetypstringkurzen: str | None = Field(default=None)
    """Kurze englische Bezeichnung der Servicetyp dieser Lehrveranstaltung."""
    servicetypstringlang: str | None = Field(default=None)
    """Lange Bezeichnung der Servicetyp dieser Lehrveranstaltung."""
    servicetypstringlangen: str | None = Field(default=None)
    """Lange englische Bezeichnung der Servicetyp dieser Lehrveranstaltung."""
    periodizitaet: int | None = Field(default=None)
    """
    Angabe, in welchem Intervall die Lehrveranstaltung abgehalten wird.
    - 0 einmalige Veranstaltung (einmalig)
    - 1 jährlich wiederkehrende Veranstaltung (jährlich)
    - 2 2-jährlich wiederkehrende Veranstaltung (2-jährlich)
    """
    periodizitaetstringkurz: str | None = Field(default=None)
    """Kurzbezeichnung für das Intervall, in dem die Lehrveranstaltung abgehalten wird."""
    periodizitaetstringkurzen: str | None = Field(default=None)
    """Englische Kurzbezeichnung für das Intervall, in dem die Lehrveranstaltung abgehalten wird."""
    periodizitaetstringlang: str | None = Field(default=None)
    """Lange Bezeichnung für das Intervall, in dem die Lehrveranstaltung abgehalten wird."""
    periodizitaetstringlangen: str | None = Field(default=None)
    """Lange englische Bezeichnung für das Intervall, in dem die Lehrveranstaltung abgehalten wird."""
    nachvereinbarung: bool | None = Field(default=None)
    """Setzt Flag ob diese Veranstaltung 'nach Vereinbarung' stattfindet"""
    dozentauswaehlen: bool | None = Field(default=None)
    """
    Entscheidet, ob der Student beim Belegen dieser
    Lehrveranstaltung einen Dozenten auswählen muss.
    Ein Student belegt in der Regel nur Lerneinheiten. Es gilt
    folgende Regel: sobald einer der beteiligten
    Lehrveranstaltungen der Lerneinheit diese Flag gesetzt hat,
    muss der Student beim Belegen einen Dozent auswählen.
    """
    spezialbewilligung: bool | None = Field(default=None)
    """
    Entscheidet, ob diese Lehrveranstaltung nur mit
    Spezialbewilligung besucht werden kann. Definiert, ob die
    Teilnahme an dieser LV eine schriftliche Genehmigung des
    Dozierenden erfordert.
    """
    externehoerer: bool | None = Field(default=None)
    """Angabe, ob diese Lehrveranstaltung für externe Hörer zugelassen ist."""
    angezeigterkommentar: str | None = Field(default=None, max_length=1000)
    """
    Diese Angabe setzt den im elektronischen
    Vorlesungsverzeichnis angzeigten Kommentar zu dieser
    Lehrveranstaltung. Dieser Kommentar hat keinen direkten
    Bezug auf den Inhalt der Lehrveranstaltung, sondern gibt
    Zusatzinformationen zu dieser Lehrveranstaltung für die
    Publikation im elektronischen Vorlesungsverzeichnis.
    Ohne englische Übersetzung
    """
    lehrveranstalter: list[Lehrveranstalter] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    """
    Liste aller Lehrveranstalter. Diese Liste hat eine
    vordefinierte Ordnung, wenn es sich um Dozenten handelt.
    Zuerst kommen die Hauptverantwortlichen in alphabetischer
    Reihenfolge, dann die anderen Dozenten in alphabetischer
    Reihenfolge. Am Schluss noch die Lehrveranstalter die
    keine Dozenten sind.
    Falls keine Lehrveranstalter erfasst sind, so wird der leere
    Array übergeben
    """
    belegungsserien: list[BelegungsserieOrt] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    """
    Abgabe der Liste der Ort und Zeitangaben für diese Lehrveranstaltung.
    Falls keine Zeitangaben erfasst sind, so wird der leere Array
    übergeben.
    """

    # NOTE: Listed in doc, but removed because not available on vvz or not relevant
    # lehrsprache: str | None = Field(default=None, max_length=2)

    # NOTE: veranstalter is excluded
    # veranstalter: list[Veranstalter] = Field(
    #     default_factory=list, sa_column=Column(JSON)
    # )
