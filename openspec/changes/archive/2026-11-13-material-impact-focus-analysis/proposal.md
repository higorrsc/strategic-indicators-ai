# Proposal: Material Impact & Effort Prioritization Analysis (Pareto / Focus Report)

## Summary

Provide financial analysts and managers with an analytical **Effort Prioritization Report** (Materiality / Pareto Focus Analysis) that highlights where management should concentrate attention based on relative percentage contribution to the whole. This analysis can be computed across three distinct segregation dimensions:

1. **Cost Center Level (`cost_center`):** Individual leaf departmental units.
2. **Hierarchy Branch Level (`hierarchy`):** Macro cost centers and executive divisions.
3. **Accounting Account Level (`accounting_account`):** Nature of expenditure (e.g., Software, Cloud, Consulting, Facilities) across the company or within a selected Cost Center.

## Motivation & Problem Statement

In corporate financial control, the Pareto Principle (80/20 rule) applies:

- Approximately 80% of budget overruns and operational expenditures originate from roughly 20% of cost centers, contracts, or accounting expense accounts.
- Looking at flat, unranked financial lists causes cognitive overload: an analyst might waste time investigating a 50% overrun on a $1,000 budget line while overlooking a 5% overrun on a $1,000,000 cloud infrastructure account.
- Crucially, knowing *where* spend occurred (Cost Center) is only half the story; analysts also need to isolate *what* was spent (Accounting Account). A Cost Center might look healthy overall while masking an alarming 300% spike in a specific accounting account.
- Currently, the API calculates indicators per cost center, but lacks:
  1. Percentage share of each entity relative to total corporate spend (`share_of_total_spent_pct`).
  2. Percentage contribution to total overruns (`share_of_total_overrun_pct`).
  3. Cumulative impact ranking (Pareto curve) to identify the vital 20% driving 80% of costs or deviations.
  4. Multi-level aggregation toggling: `cost_center`, `hierarchy`, and `accounting_account` (optionally scoped to a specific Cost Center).
  5. Action priority recommendations (`IMMEDIATE_ACTION`, `MONITOR`, `LOW_IMPACT`).

## Proposed Changes

1. **Domain Service & Analysis Logic:**
   - Implement `MaterialityAnalyzer` domain service that computes:
     - Total corporate budget and expenditure baseline for a given period.
     - Relative percentage contribution of each entity (Cost Center, Hierarchy Branch, or Accounting Account).
     - Overrun contribution percentage among critical/overrun entities.
     - Cumulative contribution percentage (`cumulative_pct`) for sorting into Pareto tiers:
       - Tier A (Top 80% of impact): `IMMEDIATE_ACTION`
       - Tier B (Next 15% of impact): `MONITOR`
       - Tier C (Remaining 5%): `LOW_IMPACT`
2. **Application Use Case:**
   - `GenerateMaterialImpactReportUseCase`: Orchestrates data retrieval, applies aggregation level (`cost_center`, `hierarchy`, or `accounting_account`), applies optional filters (e.g. `cost_center_id`), filters by focus metric (`overrun` vs `spend`), and builds a structured ranking report.
3. **Presentation & API:**
   - Endpoint: `GET /api/v1/indicators/{period}/materiality-focus`
   - Query Parameters:
     - `period`: YYYY-MM
     - `level`: `cost_center` (default), `hierarchy`, or `accounting_account`
     - `cost_center_id`: optional UUID filter when `level=accounting_account` to inspect accounts within a specific cost center
     - `metric`: `variance` (default, focusing on overruns/savings) or `spend` (focusing on total expenditure)
     - `threshold_pct`: optional cutoff (e.g., `80` for Top 80% Pareto cutoff)
4. **Export / Reporting Integration:**
   - Incorporate the materiality ranking into executive reporting and summaries.

## Out of Scope

- Automatic reallocation of budgets without user confirmation.
- Multi-year trend predictions.
