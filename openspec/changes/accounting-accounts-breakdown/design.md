# Design: Accounting Accounts Breakdown in Cost Allocation

## Context & Architectural Positioning

In Clean Architecture and Domain-Driven Design (DDD), `AccountingAccount` belongs to the `cost-allocation` bounded context. It provides classification dimensions for financial allocations without introducing general ledger complexity.

```text
Presentation Layer:
  AccountingRouter (POST/GET /api/v1/accounting-accounts)
  CostCenterAccountingBreakdownRouter (GET /api/v1/cost-centers/{id}/accounting-breakdown)
       ↓
Application Layer:
  RegisterAccountingAccountUseCase
  ListAccountingAccountsUseCase
  GetCostCenterAccountingBreakdownUseCase
       ↓
Domain Layer:
  Entity: AccountingAccount(id, code: AccountCode, name, description, is_active)
  Value Object: AccountCode (e.g., "3.1.01")
  Entity: AllocationEntry(id, cost_center_id, accounting_account_id, percentage, allocated_amount)
  Interface: AccountingAccountRepository
       ↑
Infrastructure Layer:
  SqlAlchemyAccountingAccountRepository
  Database model: accounting_accounts table
  Alembic migration: add table and FK in allocation_entries
```

## Domain Design

1. **Value Object: `AccountCode`**
   - Syntax: Dot-separated numeric groups, e.g., `^\d+(\.\d+)*$`.
   - Immutable, comparable, and validated on instantiation.
2. **Entity: `AccountingAccount`**
   - `id: UUID`
   - `code: AccountCode`
   - `name: str`
   - `description: str`
   - `is_active: bool`
   - Domain methods: `deactivate()`, `activate()`, `update_details(name, description)`.
3. **Entity: `AllocationEntry`**
   - Augment with `accounting_account_id: UUID | None` (optional for backwards compatibility with existing records, but validated when provided).
4. **Domain Invariant:**
   - Sum of `percentage` across all allocation entries on a measurement must equal exactly 100%.
   - Sum of `allocated_amount` across all allocation entries must equal gross measurement amount with penny reconciliation.

## Infrastructure & Persistence

1. **Database Schema:**
   - Table `accounting_accounts`:
     - `id`: UUID (PK)
     - `code`: VARCHAR(50) UNIQUE NOT NULL
     - `name`: VARCHAR(255) NOT NULL
     - `description`: TEXT
     - `is_active`: BOOLEAN DEFAULT TRUE NOT NULL
     - `created_at`: TIMESTAMP WITH TIME ZONE
   - Table `allocation_entries`:
     - Add `accounting_account_id`: UUID, FK to `accounting_accounts(id)`, NULLABLE (indexed).
2. **Repository Protocol:**

   ```python
   class AccountingAccountRepository(Protocol):
       async def save(self, account: AccountingAccount) -> None: ...
       async def get_by_id(self, account_id: UUID) -> AccountingAccount | None: ...
       async def get_by_code(self, code: AccountCode) -> AccountingAccount | None: ...
       async def list_all(self, active_only: bool = True, offset: int = 0, limit: int = 50) -> list[AccountingAccount]: ...
       async def count(self, active_only: bool = True) -> int: ...
   ```

## API Schemas

1. `AccountingAccountCreateRequest`:
   - `code: str` (e.g., "3.1.01")
   - `name: str`
   - `description: str | None`
2. `AccountingAccountResponse`:
   - `id: UUID`, `code: str`, `name: str`, `description: str | None`, `is_active: bool`
3. `CostCenterAccountingBreakdownResponse`:
   - `cost_center_id: UUID`, `cost_center_code: str`, `period: str`, `total_spent: Decimal`
   - `accounts: list[AccountingAccountSpendItem]`
     - `accounting_account_id: UUID`, `code: str`, `name: str`, `spent_amount: Decimal`, `share_pct: Decimal`
