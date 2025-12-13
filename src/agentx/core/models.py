"""Shared models for cross-developer interface contracts.

These models define the contracts between the infrastructure, validation,
sandbox, and evaluation layers of the AgentX framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# ============================================================
# SCHEMA MODELS (Dev 1 produces, Dev 2/3/4 consume)
# ============================================================


@dataclass
class ColumnInfo:
    """Column metadata from schema introspection."""

    name: str
    dtype: str
    nullable: bool
    primary_key: bool = False
    foreign_key: str | None = None  # "table.column" format


@dataclass
class ForeignKey:
    """Foreign key relationship metadata."""

    column: str
    references_table: str
    references_column: str
    constraint_name: str | None = None


@dataclass
class TableInfo:
    """Table metadata from schema introspection."""

    name: str
    columns: list[ColumnInfo]
    row_count: int | None = None
    schema: str = "public"


@dataclass
class SchemaSnapshot:
    """Complete schema snapshot for validation."""

    dialect: str
    database: str
    tables: dict[str, TableInfo]
    foreign_keys: dict[str, list[ForeignKey]] = field(default_factory=dict)
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_table(self, name: str) -> bool:
        """Check if a table exists in the schema."""
        return name.lower() in {t.lower() for t in self.tables}

    def has_column(self, table: str, column: str) -> bool:
        """Check if a column exists in the specified table."""
        tbl = self.tables.get(table)
        if not tbl:
            # Try case-insensitive lookup
            for t_name, t_info in self.tables.items():
                if t_name.lower() == table.lower():
                    tbl = t_info
                    break
        if not tbl:
            return False
        return column.lower() in {c.name.lower() for c in tbl.columns}

    def get_table(self, name: str) -> TableInfo | None:
        """Get table info by name (case-insensitive)."""
        if name in self.tables:
            return self.tables[name]
        for t_name, t_info in self.tables.items():
            if t_name.lower() == name.lower():
                return t_info
        return None


# ============================================================
# VALIDATION MODELS (Dev 2 produces, Dev 3/4 consume)
# ============================================================


@dataclass
class IdentifierSet:
    """Extracted SQL identifiers."""

    tables: list[str]
    columns: list[str]  # "table.column" or just "column"
    functions: list[str]
    aliases: dict[str, str] = field(default_factory=dict)  # alias -> actual name


@dataclass
class HallucinationReport:
    """Report of phantom identifiers in SQL."""

    phantom_tables: list[str]
    phantom_columns: list[str]
    phantom_functions: list[str]
    total_hallucinations: int = 0
    hallucination_score: float = 0.0  # 0.0 = none, 1.0 = all phantom

    def __post_init__(self):
        self.total_hallucinations = (
            len(self.phantom_tables)
            + len(self.phantom_columns)
            + len(self.phantom_functions)
        )


@dataclass
class ValidationResult:
    """Result of SQL validation against schema."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    hallucination_report: HallucinationReport | None = None


# ============================================================
# EXECUTION MODELS (Dev 4 produces)
# ============================================================


@dataclass
class ExecutionResult:
    """Result of SQL execution."""

    success: bool
    rows: list[dict[str, Any]]
    columns: list[str]
    row_count: int
    timing_ms: float
    error: str | None = None


@dataclass
class QueryPlan:
    """Query execution plan from EXPLAIN."""

    raw_plan: str
    estimated_cost: float | None = None
    estimated_rows: int | None = None


# ============================================================
# SCORING MODELS (Dev 4 produces)
# ============================================================


class ErrorCategory(Enum):
    """Error taxonomy categories."""

    SCHEMA_LINK = "schema_link"
    JOIN_ERROR = "join_error"
    SYNTAX_ERROR = "syntax_error"
    GROUNDING_ERROR = "grounding_error"
    TRUNCATION_ERROR = "truncation_error"
    DATA_ANALYSIS = "data_analysis"
    DOC_MISINTERPRET = "doc_misinterpret"
    UNKNOWN = "unknown"


@dataclass
class ComparisonResult:
    """Result of comparing actual vs expected results."""

    match: bool
    match_score: float  # 0.0 to 1.0
    strategy: str  # "exact", "set_based", "fuzzy", "schema_only"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiDimensionalScore:
    """Multi-dimensional evaluation score."""

    correctness: float  # 0.0 to 1.0, weight 40%
    hallucination_penalty: float  # 0.0 to 1.0, weight 25%
    efficiency: float  # 0.0 to 1.0, weight 15%
    grounding: float  # 0.0 to 1.0, weight 20%

    @property
    def weighted_total(self) -> float:
        """Calculate weighted total score."""
        return (
            self.correctness * 0.40
            + (1.0 - self.hallucination_penalty) * 0.25
            + self.efficiency * 0.15
            + self.grounding * 0.20
        )


# ============================================================
# TASK MODELS (Shared)
# ============================================================


@dataclass
class Task:
    """Evaluation task definition."""

    id: str
    question: str
    database: str
    dialect: str
    difficulty: str  # "easy", "medium", "hard", "enterprise"
    gold_sql: str
    expected_result: list[dict[str, Any]] | None = None
    tags: list[str] = field(default_factory=list)


# ============================================================
# TOOL MODELS (Dev 3 produces, Dev 4 consumes)
# ============================================================


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    data: Any
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionTrace:
    """Trace of agent session."""

    task_id: str
    tool_calls: list[dict[str, Any]]
    final_sql: str | None
    started_at: datetime
    ended_at: datetime | None = None
    total_tool_calls: int = 0
