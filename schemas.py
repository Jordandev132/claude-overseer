"""Pydantic models for Claude Overseer decision output and persistent memory."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Decision Output (what Claude returns each cycle) ──

class TaskAssignment(BaseModel):
    agent: str
    task: str
    priority: int = 1


class ContentDirective(BaseModel):
    agent: str
    platform: str
    topic: str
    angle: str = ""


class AddRemove(BaseModel):
    action: str  # "add" | "remove"
    what: str
    reason: str = ""


class ExperimentUpdate(BaseModel):
    id: str
    update: str


class CycleDecision(BaseModel):
    """Structured output Claude produces each cycle."""
    cycle_id: str
    memory_context: str = ""
    reasoning: str
    agent_actions: dict[str, str] = Field(default_factory=dict)
    task_assignments: list[TaskAssignment] = Field(default_factory=list)
    content_directives: list[ContentDirective] = Field(default_factory=list)
    add_remove: list[AddRemove] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)
    questions_for_jordan: list[str] = Field(default_factory=list)
    experiments: list[ExperimentUpdate] = Field(default_factory=list)


# ── Persistent Memory ──

class DecisionSummary(BaseModel):
    cycle: str
    summary: str
    outcome_pending: bool = True


class Experiment(BaseModel):
    id: str
    what: str
    started: str
    metric: str
    baseline: float = 0
    current: float = 0
    review_date: str = ""
    status: str = "active"


class AgentState(BaseModel):
    status: str
    since: str = ""
    reason: str = ""
    focus: str = ""
    last_leads: int = 0
    last_post: str = ""
    platform: str = ""
    queue_depth: int = 0


class ClientAlert(BaseModel):
    client: str
    alert: str
    days_until: int = 0


class Memory(BaseModel):
    """Claude's persistent brain between loops."""
    last_updated: str = ""
    last_10_decisions: list[DecisionSummary] = Field(default_factory=list)
    active_experiments: list[Experiment] = Field(default_factory=list)
    jordan_preferences: list[str] = Field(default_factory=list)
    agent_state_history: dict[str, AgentState] = Field(default_factory=dict)
    client_alerts: list[ClientAlert] = Field(default_factory=list)
    cost_this_month: float = 0
    revenue_this_month: float = 0
