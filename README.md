# AgentX: Enterprise SQL Agent Evaluation Framework

> A next-generation evaluation framework for LLM-powered SQL and data-engineering agents that surpasses Spider 2.0 through enterprise-grade realism, structural anti-hallucination mechanisms, and first-class observability.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 Motivation

Existing SQL benchmarks have critical limitations:

| Benchmark             | Limitation                                                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Spider 1.0 / BIRD** | Single SQL queries, small schemas (<50 columns), synthetic data, single dialect                                                      |
| **Spider 2.0**        | Better realism (632 tasks, 6 dialects, dbt) but only ~21% success rate for SOTA agents; limited observability into _why_ agents fail |

**AgentX** addresses these gaps with:

- **Structural hallucination prevention** via ORM-powered schema grounding
- **Multi-dimensional scoring** beyond binary pass/fail
- **Automated error taxonomy** for systematic failure analysis
- **Enterprise-scale schemas** (3,000+ columns, nested types, cross-database queries)

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           AGENTX FRAMEWORK                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      TASK ORCHESTRATOR                               │    │
│  │  • Load task definitions • Initialize environments • Coordinate flow │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │            POSTGRESQL DATA LAYER (psycopg3 — Zero ORM)               │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐    │    │
│  │  │ ConnectionPool│  │ SchemaInspect │  │ FixtureLoader         │    │    │
│  │  │ • psycopg_pool│  │ • pg_catalog  │  │ • COPY protocol       │    │    │
│  │  │ • Async ready │  │ • info_schema │  │ • Bulk streaming      │    │    │
│  │  │ • Auto-retry  │  │ • FK/PK maps  │  │ • Transactional       │    │    │
│  │  └───────────────┘  └───────────────┘  └───────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│          ┌─────────────────────────┼─────────────────────────┐              │
│          ▼                         ▼                         ▼              │
│  ┌───────────────┐    ┌─────────────────────┐    ┌───────────────────┐      │
│  │ AGENT SANDBOX │    │ HALLUCINATION       │    │ RESULT COMPARATOR │      │
│  │ • Tool APIs   │    │ DETECTOR            │    │ • Row comparison  │      │
│  │ • GetSchema   │◄───│ • sqlglot AST parse │    │ • Multi-strategy  │      │
│  │ • SampleRows  │    │ • Schema validation │    │   (exact/set/     │      │
│  │ • ValidateSQL │    │ • JOIN path verify  │    │    fuzzy/schema)  │      │
│  └───────────────┘    └─────────────────────┘    └───────────────────┘      │
│          │                         ▲                         ▲              │
│          ▼                         │                         │              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   RAW SQL EXECUTION LAYER                            │    │
│  │  • cur.execute(agent_sql) — direct PostgreSQL execution              │    │
│  │  • EXPLAIN ANALYZE capture • Timing • Error classification           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  EVALUATION SCORER              │  LOGGING & ERROR TAXONOMY          │    │
│  │  • Correctness • Hallucination  │  • Structured traces (JSONL)       │    │
│  │  • Efficiency • Grounding       │  • Auto-classification             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Design Principles

### 1. Zero ORM — Direct PostgreSQL Access

```python
# ✅ Connection pooling with psycopg3
from psycopg_pool import ConnectionPool

pool = ConnectionPool("postgresql://user:pass@localhost/db", min_size=2, max_size=10)

with pool.connection() as conn:
    # Schema introspection via catalog queries
    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'").fetchall()
    
    # Raw SQL execution for agent evaluation
    result = conn.execute(agent_generated_sql)  # Direct, no abstraction
```

### 2. Structural Hallucination Prevention

```python
class HallucinationDetector:
    def validate(self, sql: str, schema: SchemaSnapshot) -> ValidationResult:
        # Parse SQL AST → extract referenced identifiers
        # Compare against introspected schema
        # Flag phantom columns/tables/functions BEFORE execution
```

### 3. Multi-Dimensional Scoring

| Metric                  | Description                              | Weight |
| ----------------------- | ---------------------------------------- | ------ |
| `correctness`           | Result matches expected output           | 40%    |
| `hallucination_penalty` | Count of phantom identifiers             | 25%    |
| `efficiency`            | Query cost / execution time              | 15%    |
| `grounding_score`       | % of references validated against schema | 20%    |

---

## 📁 Project Structure

```
agentx/
├── README.md
├── pyproject.toml
├── docker-compose.yml              # Multi-DB local environment
│
├── src/
│   ├── agentx/
│   │   ├── __init__.py
│   │   │
│   │   ├── core/                   # Core abstractions
│   │   │   ├── task.py             # Task definition models
│   │   │   ├── agent_interface.py  # Agent protocol/ABC
│   │   │   └── config.py           # Framework configuration
│   │   │
│   │   ├── infrastructure/         # PostgreSQL Data Layer (Zero ORM)
│   │   │   ├── database_manager.py # psycopg3 connection pool
│   │   │   ├── schema_inspector.py # pg_catalog introspection
│   │   │   └── fixture_loader.py   # COPY-based bulk loading
│   │   │
│   │   ├── sandbox/                # Agent Interaction Layer
│   │   │   ├── tool_registry.py    # Tool definitions
│   │   │   ├── tools/
│   │   │   │   ├── get_schema.py
│   │   │   │   ├── sample_rows.py
│   │   │   │   ├── search_docs.py
│   │   │   │   ├── validate_sql.py
│   │   │   │   └── execute_sql.py
│   │   │   └── session.py          # Agent session management
│   │   │
│   │   ├── validation/             # Anti-Hallucination Layer
│   │   │   ├── sql_parser.py       # AST extraction (sqlglot)
│   │   │   ├── hallucination_detector.py
│   │   │   ├── schema_validator.py
│   │   │   └── join_path_verifier.py
│   │   │
│   │   ├── evaluation/             # Raw SQL Evaluation Layer
│   │   │   ├── executor.py         # Raw SQL execution
│   │   │   ├── comparators/        # Result comparison strategies
│   │   │   │   ├── exact.py
│   │   │   │   ├── set_based.py
│   │   │   │   ├── fuzzy_numeric.py
│   │   │   │   └── schema_only.py
│   │   │   ├── scorer.py           # Multi-dimensional scoring
│   │   │   └── query_analyzer.py   # EXPLAIN plan capture
│   │   │
│   │   ├── logging/                # Observability Layer
│   │   │   ├── trace_logger.py     # Structured JSONL logging
│   │   │   ├── error_taxonomy.py   # Auto-classification
│   │   │   └── metrics.py          # Aggregated statistics
│   │   │
│   │   └── orchestrator/           # Task Orchestration
│   │       ├── runner.py           # Main evaluation loop
│   │       ├── environment.py      # Per-task env setup/teardown
│   │       └── reporter.py         # Results aggregation
│   │
├── tasks/                          # Task Definitions
│   ├── schemas/                    # JSON Schema definitions
│   ├── fixtures/                   # Test data (Parquet/JSON)
│   ├── tasks.yaml                  # Task registry
│   └── gold_queries/               # Expected SQL solutions
│
├── docs/                           # External documentation corpus
│   ├── bigquery/
│   ├── snowflake/
│   └── dialect_guides/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── scripts/
    ├── setup_databases.py
    ├── run_evaluation.py
    └── generate_report.py
```

---

## 🗄️ Database

| Database   | Driver                | Features |
| ---------- | --------------------- | -------- |
| PostgreSQL | `psycopg3` + `psycopg_pool` | Connection pooling, COPY protocol, async support, EXPLAIN ANALYZE |

> **Why PostgreSQL only?** AgentX is optimized for enterprise SQL evaluation. PostgreSQL provides the best combination of:
> - Advanced query planning (`EXPLAIN ANALYZE`)
> - High-performance bulk loading (`COPY`)
> - Rich catalog introspection (`pg_catalog`, `information_schema`)
> - JSONB support for nested types

---

## 🔄 Evaluation Flow

```
1. LOAD TASK
   └── Parse task definition (question, schema, expected output, difficulty)

2. SETUP ENVIRONMENT (ORM Layer)
   ├── Create database/schema
   ├── Load fixtures via FixtureLoader
   └── Snapshot schema via SchemaInspector

3. AGENT INTERACTION (Sandbox)
   ├── Agent calls GetSchema() → ORM introspection
   ├── Agent calls SampleRows(table) → ORM query
   ├── Agent calls ValidateSQL(sql) → HallucinationDetector
   │   └── Pre-execution validation against schema snapshot
   └── Agent submits final SQL

4. EXECUTION (Raw SQL Layer)
   ├── Execute agent SQL verbatim: connection.execute(text(sql))
   ├── Capture timing, query plan, result set
   └── Execute gold SQL for comparison

5. EVALUATION (Scorer)
   ├── Compare results via selected Comparator
   ├── Calculate hallucination penalty
   ├── Compute efficiency score
   └── Aggregate multi-dimensional score

6. LOGGING (Observability)
   ├── Write structured trace (JSONL)
   ├── Classify errors into taxonomy
   └── Update aggregate metrics

7. TEARDOWN (ORM Layer)
   └── Rollback/drop test database
```

---

## 📊 Error Taxonomy

| Category           | Description                      | Detection Method               |
| ------------------ | -------------------------------- | ------------------------------ |
| `SCHEMA_LINK`      | Wrong table/column selected      | SchemaValidator mismatch       |
| `JOIN_ERROR`       | Incorrect join path or condition | JoinPathVerifier + result diff |
| `SYNTAX_ERROR`     | SQL parse failure                | sqlglot parse exception        |
| `GROUNDING_ERROR`  | Phantom column/table/function    | HallucinationDetector          |
| `TRUNCATION_ERROR` | Context window overflow          | Token count monitoring         |
| `DATA_ANALYSIS`    | Wrong aggregation/filter logic   | Result comparison failure      |
| `DOC_MISINTERPRET` | Dialect syntax confusion         | Dialect-specific pattern match |

---

## 🆚 Comparison with Spider 2.0

| Dimension                   | Spider 2.0            | AgentX                                                                | Improvement             |
| --------------------------- | --------------------- | --------------------------------------------------------------------- | ----------------------- |
| **Hallucination Detection** | Post-execution only   | Pre-execution schema validation via `pg_catalog`                      | Structural prevention   |
| **Scoring**                 | Binary pass/fail      | Multi-dimensional (correctness, hallucination, efficiency, grounding) | Root-cause visibility   |
| **Database Layer**          | Mixed/unspecified     | Zero-ORM psycopg3 with connection pooling                             | Performance + simplicity|
| **Fixture Loading**         | Varies                | PostgreSQL `COPY` protocol (fastest bulk load)                        | Deterministic + fast    |
| **Error Analysis**          | Manual categorization | Automated taxonomy classification                                     | Scalable analysis       |
| **Schema Introspection**    | Framework-dependent   | Direct `pg_catalog` queries (no ORM overhead)                         | Enterprise support      |

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/ashcastelinocs124/AgentX-Hackathon.git
cd AgentX-Hackathon

# Install dependencies
pip install -e ".[dev]"

# Start local databases
docker-compose up -d

# Run evaluation
python scripts/run_evaluation.py --tasks tasks/tasks.yaml --agent your_agent
```

---

## 📅 Implementation Roadmap

### Phase 1: PostgreSQL Data Layer (Weeks 1-2)

- `DatabaseManager` with psycopg3 connection pool
- `SchemaInspector` using `pg_catalog` queries
- Docker Compose for local PostgreSQL
- Configuration system

### Phase 2: Schema Introspection & Fixtures (Weeks 3-4)

- Complete schema introspection (tables, columns, FKs, PKs)
- `FixtureLoader` with PostgreSQL `COPY` protocol
- Transactional setup/teardown via savepoints

### Phase 3: Hallucination Detection (Weeks 5-6)

- SQL AST parser using `sqlglot`
- `SchemaValidator` and `HallucinationDetector`
- `JoinPathVerifier`

### Phase 4: Agent Sandbox (Weeks 7-8)

- Tool protocol definition
- GetSchema, SampleRows, ValidateSQL, ExecuteSQL tools
- Session management with state tracking

### Phase 5: Evaluation Pipeline (Weeks 9-11)

- Raw SQL executor with `EXPLAIN ANALYZE` capture
- Result comparators (exact, set, fuzzy, schema-only)
- Multi-dimensional scorer
- Structured logging and error taxonomy

### Phase 6: Polish & Production (Weeks 12-14)

- CLI runner and reporter
- Metrics dashboard
- Documentation and testing
- Performance optimization

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines before submitting PRs.

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
ruff check src/
```

---

## 📚 References

- [Spider 2.0 Paper](https://arxiv.org/abs/2411.07763)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [sqlglot Documentation](https://sqlglot.com/)
