Feature: Strategic Budget Indicators System
  As a financial executive and controller
  I want to manage hierarchical cost centers, set budget targets, allocate contract expenses with exact pennies, compute variance indicators, simulate what-if scenarios, and receive AI-powered executive insights.

  Scenario: Hierarchical cost center management and budget aggregation
    Given a root cost center with code "1.0" and name "Executive Board"
    And a child cost center with code "1.1" and name "IT Operations" under "1.0"
    When planned budget of 20000.00 is set for cost center "1.0" in period "2026-03"
    And planned budget of 30000.00 is set for cost center "1.1" in period "2026-03"
    Then the consolidated hierarchical budget for cost center "1.0" in period "2026-03" is 50000.00

  Scenario: Contract registration and exact penny cost allocation
    Given active cost centers "1.1", "1.2", and "1.3"
    And a registered vendor contract "CT-2026-001" with default split 33.34%, 33.33%, and 33.33%
    When a measurement with gross amount 1000.00 is submitted for period "2026-03"
    Then the measurement is in "SUBMITTED" state
    And the allocation entries reconcile to exact amounts 333.40, 333.30, and 333.30
    When the measurement is approved
    Then the measurement transitions to "APPROVED" state

  Scenario: Deterministic budget variance and threshold calculation
    Given cost center "1.1" has a budget target of 50000.00 in period "2026-03"
    And approved allocation measurements totaling 35000.00 for period "2026-03"
    When period indicators are computed for period "2026-03"
    Then cost center "1.1" has actual expenditure 35000.00
    And the variance is -15000.00 with execution rate 70.0%
    And the indicator status is "NORMAL"

  Scenario: What-If simulation under supplier cost inflation
    Given cost center "1.1" with budget 50000.00 and actual baseline expenditure 35000.00
    When a what-if scenario is simulated with 50% inflation on contract "CT-2026-001"
    Then the simulated actual expenditure for cost center "1.1" becomes 52500.00
    And a new budget overrun is identified

  Scenario: Allocation anomaly detection and AI executive summary
    Given a contract with historical average allocation of 5% to cost center "1.1"
    When a new measurement is submitted with a 45% allocation share to cost center "1.1"
    Then the system flags an "ABRUPT_ALLOCATION_SHIFT" anomaly with "HIGH" severity
    When an executive summary is generated for the period
    Then the summary report identifies root causes and strategic recommendations
