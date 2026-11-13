# Proposal: Accounting Accounts Breakdown in Cost Allocation

## Summary

Introduce the concept of **Accounting Accounts** (Contas Contábeis / Plano de Contas) into the financial cost allocation and measurement domain. This allows measurements allocated to a Cost Center to be explicitly subdivided into one or more Accounting Accounts (e.g., `3.1.01 - Licenciamento de Software`, `3.1.02 - Infraestrutura Cloud`, `3.1.05 - Serviços de Consultoria`), providing granular visibility into what types of expenses constitute the cost center's consumption.

## Motivation & Problem Statement

Currently, a `Measurement` allocates gross expenditures exclusively to Cost Centers via `AllocationEntry(cost_center_id, percentage, allocated_amount)`. While this satisfies departmental budget tracking, corporate controllership and financial analysts require multidimensional visibility:

1. Knowing **where** the money was spent (the Cost Center).
2. Knowing **what nature of expense** was incurred (the Accounting Account).
3. Ensuring that a Cost Center's expenditures can be audited, grouped, and filtered by specific accounting accounts without altering top-level budget reconciliation.

## Proposed Changes

1. **Domain Model:**
   - Create `AccountingAccount` entity with identity, code (`AccountCode` value object supporting format like `3.1.01` or `4.1.02.001`), name, description, and status (`ACTIVE`/`INACTIVE`).
   - Augment `AllocationEntry` or introduce an account-level breakdown linking `(cost_center_id, accounting_account_id, percentage, allocated_amount)`.
   - Validate that allocations across cost centers and their accounting accounts preserve exact-penny monetary integrity.
2. **Persistence & Database:**
   - Create `accounting_accounts` table and add `accounting_account_id` foreign key to `allocation_entries`.
   - Generate Alembic migration.
   - Implement `AccountingAccountRepository` with SQLAlchemy and asyncpg.
3. **Application & Use Cases:**
   - `RegisterAccountingAccountUseCase`: Register and list accounting accounts with pagination and filtering.
   - `GetCostCenterAccountingBreakdownUseCase`: Provide expenditures of a Cost Center for a given period partitioned by accounting account.
   - Update `SubmitMeasurementUseCase` and `RegisterContractUseCase` to support optional/required accounting account association.
4. **Presentation & API:**
   - New router `POST /api/v1/accounting-accounts` and `GET /api/v1/accounting-accounts`.
   - New query endpoint `GET /api/v1/cost-centers/{cost_center_id}/accounting-breakdown?period=YYYY-MM`.
   - Update measurement allocation payload schemas to accept `accounting_account_id`.

## Out of Scope

- General ledger double-entry bookkeeping (crediting/debiting asset and liability accounts).
- Modifying historical approved measurements from prior periods.
