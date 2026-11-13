"""Indicators application use cases package.

Architecture Note (CQRS):
The Strategic Indicators bounded context operates strictly as a read-only
analytical projection. It consumes data from upstream operational contexts
(Allocation and Budgeting) to compute deterministic variance metrics,
materiality rankings, and What-If simulations. As such, it contains only
queries under the queries/ subpackage, with no mutation commands.
"""
