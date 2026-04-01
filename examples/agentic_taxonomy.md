# Five Agent Roles Working in Concert

Series: Agentic Taxonomy
Subtitle: A Business-Oriented Framework for Intelligent Workflows

## 01 – Assistant (Interface Layer)

**Role:** Supports users with discrete, well-defined tasks (drafting, summarizing, answering queries).

**Decision Path:** Use when the workflow requires information retrieval, content generation, or question answering without complex reasoning or system actions.

## 02 – Analyst (Cognitive/Reasoning Layer)

**Role:** Transforms data into insight—analyzes, forecasts, simulates, and recommends.

**Decision Path:** Deploy when the workflow demands interpretation, pattern recognition, or higher-order analysis (e.g., scenario modeling, risk assessment).

## 03 – Tasker (Execution/Actuator Layer)

**Role:** Takes bounded, deterministic actions—updates records, triggers workflows, executes code, etc.

**Decision Path:** Use when the workflow needs to make actual changes in systems or trigger downstream processes. Requires the highest level of guardrails, auditability, and security.

## 04 – Orchestrator (Control Plane)

**Role:** Manages end-to-end workflows—decomposes objectives, delegates to other agents, handles task sequencing and coordination.

**Decision Path:** Always use when coordinating multi-step, multi-agent workflows or integrating across multiple systems/domains. Essential for scalability and traceability.

## 05 – Guardian (Governance/Compliance Layer)

**Role:** Enforces policies, monitors for compliance, audits actions, and detects anomalies.

**Decision Path:** Use in any workflow where auditability, quality, or regulatory compliance is required. Integrate escalation paths for human oversight on high-risk or low-confidence outputs.

## Building Trust & Auditability

Why separating concerns is critical:
- Isolates functions: Assistant/Analyst (Read only) from Tasker (Write/Action)
- Ensures source validation & prevents hallucinations
- Implements automated anomaly detection (ML or Rule-Based)
- Facilitates Human-over-the-loop governance for high-stakes decisions
