## ADDED Requirements

### Requirement: Guided decision-making for deploy and infrastructure topics the user has not mastered
Decisions regarding deploy topology, VPS provider selection, and domain/DNS acquisition SHALL be conducted through a guided, didactic mentoring session (via the `backend-mentor` skill) rather than being decided or executed autonomously, per the existing restriction in `PROMPT_REFINADO.md`'s `<deploy_infraestrutura>` section.

#### Scenario: Deploy decision requires mentoring
- **WHEN** a decision about deploy topology, VPS provider, or domain/DNS purchase needs to be made
- **THEN** the `backend-mentor` skill is invoked to explain the options and trade-offs didactically before any decision is finalized or any resource with real-world cost is created

#### Scenario: No unattended real-money spend
- **WHEN** an action would incur a real financial cost (e.g., purchasing a domain, provisioning a billable VPS or cloud resource)
- **THEN** the user gives explicit confirmation after the guided explanation, before the action is executed

### Requirement: Real system deploy target is a VPS, not AWS-managed infrastructure
The system's actual deploy (Django, FastAPI microservices, MongoDB, Redis) SHALL run on a VPS via Docker Compose. AWS SHALL NOT be used to host the backend for this system.

#### Scenario: Deploy configuration is inspected
- **WHEN** the repository's deploy configuration is inspected
- **THEN** it targets a VPS (Docker Compose based deploy), with no Terraform or AWS compute/networking resources defined for the backend

### Requirement: Static frontend hosting on AWS S3
The React SPA frontend SHALL be built as a static bundle and hosted on an AWS S3 bucket configured for static website hosting. This is the one confirmed use of AWS in the system's real deploy path.

#### Scenario: Frontend deploy pipeline exists
- **WHEN** the frontend build/deploy pipeline is inspected
- **THEN** it produces a static build and uploads it to an S3 bucket, with no other AWS compute resource involved

### Requirement: Terraform + AWS infrastructure learning is decoupled from this system's deploy
Terraform and AWS infrastructure-as-code SHALL be pursued as a separate, smaller, dedicated learning project, decoupled from and not blocking this system's real deploy (which targets a VPS). No Terraform module for this system's production backend infrastructure is required by this capability.

#### Scenario: Terraform learning does not block system deploy
- **WHEN** the VPS-based deploy of this system is implemented
- **THEN** it does not depend on any Terraform module or AWS backend-infrastructure resource being created first

### Requirement: Guided decision-making for observability instrumentation
Decisions about what to instrument first with Prometheus and how to structure Grafana dashboards SHALL be conducted through the same guided, didactic mentoring approach as the deploy decisions above, per `PROMPT_REFINADO.md`'s `<observabilidade>` section.

#### Scenario: Observability decision requires mentoring
- **WHEN** a decision about which metrics to expose or which dashboard to build first needs to be made
- **THEN** the `backend-mentor` skill is invoked to explain the options didactically before implementation begins
