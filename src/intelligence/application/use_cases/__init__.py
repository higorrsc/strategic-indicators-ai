"""Intelligence application use cases package.

Architecture Note (CQRS):
The Strategic Intelligence bounded context operates as a cognitive and
analytical projection layer. It synthesizes indicators and historical
allocations to detect anomalies and generate AI executive summaries.
All use cases in this context are organized as queries under the queries/
subpackage, with no mutation commands.
"""
