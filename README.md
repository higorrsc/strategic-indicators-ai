# Strategic Indicators — SDD & AI

**Spec-Driven Development · AI Agents · OpenAPI · BDD · LLM**

A project focused on exploring **Spec-Driven Development combined with AI-assisted software engineering**.

The application crosses process data with artificial intelligence to generate **executive-level insights and strategic indicators**.

The main experiment is not only the resulting application, but the development process itself.

## Specification First

The API is specified before implementation.

Possible approaches include:

- OpenAPI / Swagger
- BDD
- `pytest-bdd`
- `behave`

The specification defines:

- Endpoints
- HTTP methods
- Request schemas
- Response schemas
- Pydantic models
- Business rules
- Acceptance criteria

```text
             Specification
                  │
                  ▼
          ┌───────────────┐
          │    OpenAPI    │
          │   / BDD Specs │
          └───────┬───────┘
                  │
                  ▼
            AI Development
                  │
                  ▼
          ┌───────────────┐
          │ Controllers   │
          │ Use Cases     │
          │ Repositories  │
          └───────┬───────┘
                  │
                  ▼
              Test Suite
                  │
           ┌──────┴──────┐
           │             │
         PASS           FAIL
           │             │
           ▼             ▼
        Complete       Error Log
                         │
                         ▼
                    AI Correction
                         │
                         └──────► Test
```

## AI-assisted development

An AI coding agent is given the specification and instructed to implement the application based exclusively on the defined behavior.

Potential tools include:

- Cursor
- Aider
- GitHub Copilot
- Other coding agents

The agent is expected to respect:

- SOLID
- Clean Architecture
- Defined interfaces
- API contracts
- Acceptance criteria
- Existing tests

## Validation loop

Generated code is validated through automated tests.

When a test fails:

1. Capture the failure.
2. Provide the error/log to the agent.
3. Let the agent analyze the failure.
4. Apply the correction.
5. Execute the test suite again.
6. Repeat until the specified behavior is satisfied.

This project therefore explores the relationship between:

**Specification → AI Agent → Implementation → Tests → Feedback → Refinement**
