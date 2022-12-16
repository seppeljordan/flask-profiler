from __future__ import annotations

import datetime
from dataclasses import dataclass, replace
from typing import Any, List, Optional, Protocol, Union


class Expression(Protocol):
    def as_expression(self) -> str:
        ...


class FromClause(Protocol):
    def as_from_clause(self) -> str:
        ...


class SelectorClause(Protocol):
    def as_selector_clause(self) -> str:
        ...


class Query(Protocol):
    def as_query(self) -> str:
        ...


class Vector(Protocol):
    def as_vector(self) -> str:
        ...


class Selector(Protocol):
    def as_selector(self) -> str:
        ...


# Implementation


@dataclass
class SelectQueryImpl:
    selector: SelectorClause
    from_clause: FromClause
    where_clause: Optional[Expression] = None
    group_by: Optional[Expression] = None
    limit_clause: Optional[int] = None
    offset_clause: Optional[int] = None

    def as_query(self) -> str:
        query = "SELECT " + self.selector.as_selector_clause()
        query += " FROM " + self.from_clause.as_from_clause()
        if self.where_clause is not None:
            query += " WHERE " + self.where_clause.as_expression()
        if self.group_by is not None:
            query += " GROUP BY " + self.group_by.as_expression()
        if self.limit_clause is not None:
            query += f" LIMIT {self.limit_clause}"
        if self.offset_clause is not None:
            query += f" OFFSET {self.offset_clause}"
        return query

    def as_vector(self) -> str:
        return self.as_query()

    def limit(self, n) -> SelectQueryImpl:
        return replace(
            self,
            limit_clause=n,
        )

    def offset(self, n) -> SelectQueryImpl:
        return replace(
            self,
            offset_clause=n,
        )

    def and_where(self, expression: Expression) -> SelectQueryImpl:
        return replace(
            self,
            where_clause=expression
            if self.where_clause is None
            else BinaryOp("AND", self.where_clause, expression),
        )

    def __str__(self) -> str:
        return self.as_query()


@dataclass
class BinaryOp:
    operator: str
    x: Expression
    y: Expression

    def as_expression(self) -> str:
        return f"({self.x.as_expression()}) {self.operator} ({self.y.as_expression()})"

    def as_selector(self) -> str:
        return self.as_expression()


@dataclass
class Literal:
    value: Any

    def as_expression(self) -> str:
        if isinstance(self.value, int):
            return str(self.value)
        elif isinstance(self.value, float):
            return str(self.value)
        elif isinstance(self.value, (datetime.date, datetime.datetime)):
            return f"'{self.value.isoformat()}'"
        else:
            escaped = str(self.value).replace("'", "''")
            return f"'{escaped}'"

    def as_selector(self) -> str:
        return self.as_expression()


@dataclass
class Identifier:
    names: Union[str, List[str]]

    def as_expression(self) -> str:
        if isinstance(self.names, str):
            return self.escape(self.names)
        else:
            return ".".join(map(self.escape, self.names))

    def as_from_clause(self) -> str:
        return self.as_expression()

    def as_selector(self) -> str:
        return self.as_expression()

    @staticmethod
    def escape(value: str):
        escaped = value.replace('"', '""')
        return f'"{escaped}"'


@dataclass
class ExpressionList:
    expressions: List[Expression]

    def as_expression(self) -> str:
        if self.expressions:
            return ", ".join(x.as_expression() for x in self.expressions)
        else:
            return "NULL"


@dataclass
class Alias:
    expression: Query
    name: Identifier

    def as_from_clause(self) -> str:
        return f"({self.expression.as_query()}) AS {self.name.as_expression()}"


@dataclass
class SelectorList:
    selectors: List[Selector]

    def as_selector_clause(self) -> str:
        return ", ".join(x.as_selector() for x in self.selectors)


class All:
    def as_selector(self) -> str:
        return "*"


@dataclass
class Aggregate:
    name: str
    expression: Union[Expression, All]
    is_distinct: bool = False

    def as_selector(self) -> str:
        result = f"{self.name}("
        if self.is_distinct:
            result += "DISTINCT "
        if isinstance(self.expression, All):
            result += self.expression.as_selector()
        else:
            result += self.expression.as_expression()
        result += ")"
        return result
