"""
A2A (Agent-to-Agent) Protocol Interface for AgentX SQL Benchmark.

This module provides a standardized interface for external agents to:
1. Discover available evaluation tasks
2. Submit SQL queries for evaluation
3. Receive detailed scoring feedback

Compliant with common agent communication patterns.
"""

from .server import A2AServer, create_app
from .models import (
    TaskRequest,
    TaskResponse,
    EvaluationRequest,
    EvaluationResponse,
    AgentInfo,
    BenchmarkInfo,
)
from .client import A2AClient

__all__ = [
    "A2AServer",
    "create_app",
    "TaskRequest",
    "TaskResponse",
    "EvaluationRequest",
    "EvaluationResponse",
    "AgentInfo",
    "BenchmarkInfo",
    "A2AClient",
]
