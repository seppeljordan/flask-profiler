from __future__ import annotations

import datetime
import enum
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


class Statement(Protocol):
    def as_statement(self) -> str:
        ...


class PragmaValue(Protocol):
    def as_pragma_value(self) -> str:
        ...


class ColumnConstraint(Protocol):
    def as_column_constraint(self) -> str:
        ...


# Statements


@dataclass
class Select:
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

    def limit(self, n) -> Select:
        return replace(
            self,
            limit_clause=n,
        )

    def offset(self, n) -> Select:
        return replace(
            self,
            offset_clause=n,
        )

    def and_where(self, expression: Expression) -> Select:
        return replace(
            self,
            where_clause=expression
            if self.where_clause is None
            else BinaryOp("AND", self.where_clause, expression),
        )

    def __str__(self) -> str:
        return self.as_query()

    def as_statement(self) -> str:
        return str(self)


@dataclass(frozen=True)
class Insert:
    into: Identifier
    rows: List[List[Expression]]
    columns: Optional[List[Identifier]] = None
    alias: Optional[Identifier] = None

    def __str__(self) -> str:
        statement = f"INSERT INTO {self.into.as_expression()} "
        if self.alias is not None:
            statement += f"AS {self.alias.as_expression()} "
        if self.columns is not None:
            statement += (
                "(" + ",".join(map(lambda c: c.as_expression(), self.columns)) + ") "
            )
        statement += "VALUES "
        statement += ", ".join(
            "(" + ", ".join(value.as_expression() for value in row) + ")"
            for row in self.rows
        )
        return statement

    def as_statement(self) -> str:
        return str(self)


@dataclass
class Pragma:
    name: str
    schema: Optional[str] = None
    value: Optional[PragmaValue] = None

    def __str__(self) -> str:
        statement = "PRAGMA "
        if self.schema is not None:
            statement += self.schema + "."
        statement += self.name
        if self.value is not None:
            statement += f" = {self.value.as_pragma_value()}"
        return statement

    def as_statement(self) -> str:
        return str(self)


@dataclass
class CreateTable:
    name: Identifier
    columns: List[ColumnDefinition]
    if_not_exists: bool = False

    def __str__(self) -> str:
        statement = "CREATE TABLE "
        if self.if_not_exists:
            statement += "IF NOT EXISTS "
        statement += str(self.name) + " (" + ", ".join(map(str, self.columns)) + ")"
        return statement

    def as_statement(self) -> str:
        return str(self)


@dataclass
class CreateIndex:
    name: Identifier
    on: Identifier
    indices: List[IndexDefinition]
    if_not_exists: bool = False

    def __str__(self) -> str:
        statement = f"CREATE INDEX {self.name} ON {self.on} ("
        statement += ", ".join(map(str, self.indices)) + ")"
        return statement

    def as_statement(self) -> str:
        return str(self)


@dataclass
class Delete:
    table: Identifier
    where: Optional[Expression] = None

    def __str__(self) -> str:
        statement = f"DELETE FROM {self.table}"
        if self.where:
            statement += f" {self.where.as_expression()}"
        return statement

    def as_statement(self) -> str:
        return str(self)


# Details


@dataclass
class IndexDefinition:
    column: Expression
    descending: bool = False

    def __str__(self) -> str:
        definition = self.column.as_expression()
        if self.descending:
            definition += " DESC"
        return definition


@dataclass
class ColumnDefinition:
    name: Identifier
    column_type: ColumnType
    constraints: Optional[List[ColumnConstraint]] = None

    def __str__(self) -> str:
        definition = f"{self.name} {self.column_type.as_type_def()}"
        if self.constraints:
            definition += " " + " ".join(
                constraint.as_column_constraint() for constraint in self.constraints
            )
        return definition


class ColumnType(enum.Enum):
    NULL = "NULL"
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"
    BLOB = "BLOB"

    def as_type_def(self) -> str:
        return self.value


@dataclass
class PrimaryKey:
    autoincrement: bool = False

    def __str__(self) -> str:
        constraint = "PRIMARY KEY"
        if self.autoincrement:
            constraint += " AUTOINCREMENT"
        return constraint

    def as_column_constraint(self) -> str:
        return str(self)


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

    def as_pragma_value(self) -> str:
        return self.as_expression()


@dataclass
class Identifier:
    names: Union[str, List[str]]

    def __str__(self) -> str:
        if isinstance(self.names, str):
            return self.escape(self.names)
        else:
            return ".".join(map(self.escape, self.names))

    def as_expression(self) -> str:
        return str(self)

    def as_from_clause(self) -> str:
        return str(self)

    def as_selector(self) -> str:
        return str(self)

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
            return str(null)


class Null:
    def __str__(self) -> str:
        return "NULL"

    def as_expression(self) -> str:
        return str(self)

    def as_pragma_value(self) -> str:
        return str(self)


null = Null()


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
