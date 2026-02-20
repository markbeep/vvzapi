from enum import Enum
from typing import Generator, Sequence, cast, get_args, override
from typing import Literal as TLiteral

from opentelemetry import trace
from pydantic import BaseModel
from pyparsing import (
    Group,
    Literal,
    NotAny,
    Optional,
    QuotedString,
    Word,
    alphas,
    infixNotation,
    opAssoc,
    printables,
)
from rapidfuzz import fuzz, process, utils

tracer = trace.get_tracer(__name__)

ParsedType = Sequence["ParsedType | str"]

# TODO: add more keys
QueryKey = TLiteral[
    "title",
    "title_german",
    "title_english",
    "number",
    "credits",
    "year",
    "semester",
    "lecturer",
    "descriptions",
    "descriptions_german",
    "descriptions_english",
    "level",
    "department",
    "language",
    "offered",
    "examtype",
    "coursereview",
]

mapping: dict[str, QueryKey] = {
    "t": "title",
    "n": "number",
    "c": "credits",
    "mv": "credits",
    "ects": "credits",
    "tg": "title_german",
    "te": "title_english",
    "y": "year",
    "s": "semester",
    "l": "lecturer",
    "i": "lecturer",
    "instructor": "lecturer",
    "d": "descriptions",
    "dg": "descriptions_german",
    "de": "descriptions_english",
    "dep": "department",
    "lvl": "level",
    "lev": "level",
    "lang": "language",
    "offeredin": "offered",
    "o": "offered",
    "off": "offered",
    "e": "examtype",
    "cr": "coursereview",
}


class Operator(str, Enum):
    eq = "="
    ne = "!="
    gt = ">"
    lt = "<"
    ge = ">="
    le = "<="

    @override
    def __str__(self) -> str:
        return self.value


class FilterOperator(BaseModel):
    key: QueryKey
    operator: Operator
    value: str

    @override
    def __str__(self) -> str:
        val = (
            f'"{self.value}"'
            if " " in self.value or '"' in self.value
            else f"'{self.value}'"
        )
        return f"{self.key}{self.operator}{val}"


class LogicalOperator(BaseModel):
    ops: list["FilterOperator | AND | OR"]

    @override
    def __iter__(self) -> Generator[FilterOperator, None, None]:  # pyright: ignore[reportIncompatibleMethodOverride]
        for op in self.ops:
            if isinstance(op, FilterOperator):
                yield op
            else:
                yield from op

    @override
    def __str__(self) -> str:
        result = ""
        for i, op in enumerate(self.ops):
            if i > 0:
                result += f" {self.__class__.__name__.lower()} "  # AND / OR
            if isinstance(op, (AND, OR)):
                result += f"({str(op)})"
            else:
                result += str(op)
        return result

    @override
    def __repr__(self) -> str:
        def _format_ops(ops: list["FilterOperator | AND | OR"], indent: int = 0) -> str:
            lines: list[str] = []
            for op in ops:
                if isinstance(op, (AND, OR)):
                    lines.append(" " * indent + f"{op.__class__.__name__.lower()}:")
                    lines.append(_format_ops(op.ops, indent + 2))
                else:
                    lines.append(" " * indent + str(op))
            return "\n".join(lines)

        return _format_ops(self.ops)


class OR(LogicalOperator):
    pass


class AND(LogicalOperator):
    pass


def _find_closest_operators(key: str) -> QueryKey | None:
    """Best effort to try to figure out what key a user meant"""
    with tracer.start_as_current_span("find_closest_operators") as span:
        span.set_attribute("key", key)
        key = key.lower()
        if key in mapping:
            result = mapping[key]
            span.set_attribute("matched", str(result))
            return result

        args = cast(Sequence[QueryKey], get_args(QueryKey))

        if key in args:
            result = cast(QueryKey, key)
            span.set_attribute("matched", str(result))
            return result

        # first see if there's a key that starts the same
        for query_key in args:
            if query_key.startswith(key):
                span.set_attribute("matched", str(query_key))
                return query_key

        # try to figure out the closest match
        if result := process.extractOne(
            key,
            args,
            scorer=fuzz.partial_ratio,
            processor=utils.default_process,
        ):
            matched_name, score, _ = result
            if score >= 60:
                span.set_attribute("matched", str(matched_name))
                span.set_attribute("match_score", score)
                return matched_name
        span.set_attribute("matched", "None")
        return None


def _negated_operator(op: Operator) -> Operator:
    match op:
        case Operator.eq:
            return Operator.ne
        case Operator.ne:
            return Operator.eq
        case Operator.gt:
            return Operator.le
        case Operator.ge:
            return Operator.lt
        case Operator.lt:
            return Operator.ge
        case Operator.le:
            return Operator.gt


def _parse_operator(item: ParsedType) -> FilterOperator | None:
    match item:
        case [str(key), ":", str(value)]:  # o:value
            key_mapped = _find_closest_operators(key)
            if not key_mapped:
                return None
            return FilterOperator(
                key=key_mapped,
                operator=Operator.eq,
                value=value,
            )
        case ["-", str(key), ":", str(value)]:  # -o:value
            key_mapped = _find_closest_operators(key)
            if not key_mapped:
                return None
            return FilterOperator(
                key=key_mapped,
                operator=Operator.ne,
                value=value,
            )
        case [str(key), ("=" | "!=" | ">" | "<" | ">=" | "<=") as operator, str(value)]:
            # o=val, o!=val, o>val, o<val, ...
            key_mapped = _find_closest_operators(key)
            if not key_mapped:
                return None
            return FilterOperator(
                key=key_mapped,
                operator=Operator(operator),
                value=value,
            )
        case [
            "-",
            str(key),
            ("=" | "!=" | ">" | "<" | ">=" | "<=") as operator,
            str(value),
        ]:
            # -o=val, -o!=val, -o>val, -o<val, ...
            key_mapped = _find_closest_operators(key)
            if not key_mapped:
                return None
            return FilterOperator(
                key=key_mapped,
                operator=_negated_operator(Operator(operator)),
                value=value,
            )
        case ["-", str(value)]:  # -val
            return FilterOperator(
                key="title",
                operator=Operator.ne,
                value=value,
            )
        case [str(value)]:  # val
            return FilterOperator(
                key="title",
                operator=Operator.eq,
                value=value,
            )
        case _:
            return None


def _build_ops(parsed: ParsedType) -> AND | OR:
    with tracer.start_as_current_span("build_ops"):
        ops: list[FilterOperator | AND | OR] = []
        ored = "OR" in parsed or "or" in parsed
        for item in parsed:
            if isinstance(item, str) and (
                item.lower() == "or" or item.lower() == "and"
            ):
                continue
            unparsed = _parse_operator(item)
            if unparsed:
                ops.append(unparsed)
            else:
                ops.append(_build_ops(item))
        return OR(ops=ops) if ored else AND(ops=ops)


def _parse_query(query: str) -> ParsedType:
    with tracer.start_as_current_span("parse_query") as span:
        span.set_attribute("query", query)
        key = Word(alphas, alphas + "_")
        unquoted = Word(printables, excludeChars="()")
        quoted = QuotedString('"') | QuotedString("'")
        operand = quoted | unquoted
        # NOTE: ensure order of operators from longest to shortest to prevent parsing issues
        operator = (
            Literal("!=")
            | Literal(">=")
            | Literal("<=")
            | Literal(":")
            | Literal("=")
            | Literal(">")
            | Literal("<")
        )
        operator_term = Group(Optional(Literal("-")) + key + operator + operand)
        plain_term = Group(Optional(Literal("-")) + operand)

        or_literal = Literal("OR") | Literal("or")
        and_literal = Literal("AND") | Literal("and")

        implicit_and = Optional(and_literal) + NotAny(or_literal)

        term = operator_term | plain_term
        parser = infixNotation(
            term,
            [
                (implicit_and, 2, opAssoc.LEFT),
                (or_literal, 2, opAssoc.LEFT),
            ],
        )
        return (
            parser.parseString(query).asList()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        )


def build_search_operators(query: str) -> AND | OR:
    with tracer.start_as_current_span("build_search_operators") as span:
        span.set_attribute("query", query)
        parsed = _parse_query(query)
        result = _build_ops(parsed)
        span.set_attribute("operator_type", result.__class__.__name__)
        span.set_attribute("operator_count", len(result.ops))
        return result
