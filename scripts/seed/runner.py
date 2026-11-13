"""CLI execution runner and console reporting for data seeding."""

from __future__ import annotations

import argparse
import asyncio

from src.intelligence.application.dto import ExecutiveSummaryDTO
from src.presentation.dependencies import DependencyContainer
from src.shared.config.settings import get_settings

from .seeder import seed_data


def print_executive_briefing(summary: ExecutiveSummaryDTO) -> None:
    """Print an executive briefing to stdout."""
    status_icon = "🚨" if summary.financial_health_status == "CRITICAL" else "⚠️"
    print("\n" + "=" * 78)
    print(
        f" {status_icon} STRATEGIC FINANCIAL EXECUTIVE BRIEFING "
        f"— PERIOD {summary.period}"
    )
    print("=" * 78)
    print(f"\n[Financial Health Status]: {summary.financial_health_status}")
    print(f"[AI Provider]: {summary.ai_provider} (Fallback: {summary.is_fallback})")

    print("\n[Executive Synthesis]:")
    print(f"  {summary.executive_summary}")

    print("\n[Identified Root Causes]:")
    for idx, rc in enumerate(summary.root_causes, 1):
        print(f"  {idx}. {rc}")

    print("\n[Strategic Action Recommendations]:")
    for idx, rec in enumerate(summary.strategic_recommendations, 1):
        print(f"  {idx}. {rec}")

    print("\n[Detected Allocation Anomalies]:")
    if summary.anomalies:
        for idx, a in enumerate(summary.anomalies, 1):
            print(
                f"  {idx}. [{a.anomaly_type}] Cost Center: "
                f"{a.cost_center_id} — {a.description}"
            )
    else:
        print("  None detected.")

    print("\n[Planned vs. Actual Indicators Summary]:")
    print(
        f"  Total Budgeted: ${summary.indicators_summary.total_budgeted} | "
        f"Total Actual: ${summary.indicators_summary.total_actual} | "
        f"Net Variance: ${summary.indicators_summary.total_variance}"
    )
    print("  " + "-" * 74)
    print(
        f"  {'Cost Center':<14} | {'Budgeted':<14} | {'Actual':<14} | "
        f"{'Rate':<8} | {'Status'}"
    )
    print("  " + "-" * 74)
    for ind in summary.indicators_summary.indicators:
        print(
            f"  {ind.cost_center_code:<14} | "
            f"${ind.budgeted_amount:<13} | "
            f"${ind.actual_amount:<13} | "
            f"{ind.execution_rate:>6.1f}% | "
            f"{ind.status}"
        )
    print("=" * 78 + "\n")


async def run_seed_and_analysis(
    database_url: str | None = None,
    clean: bool = False,
    no_ai: bool = False,
    period: str = "2026-03",
    lang: str = "pt-br",
    echo: bool = False,
) -> ExecutiveSummaryDTO | None:
    """Run seeding lifecycle within a session-managed dependency container."""
    settings = get_settings()
    url = database_url or settings.DATABASE_URL

    container = DependencyContainer()
    print(f"🔌 Connecting to database: {url}")
    await container.init_database(database_url=url, echo=echo)

    try:
        summary = await seed_data(
            container=container,
            clean=clean,
            run_ai=not no_ai,
            target_period_str=period,
            language_str=lang,
        )
        if summary is not None:
            print_executive_briefing(summary)
        return summary
    finally:
        await container.close_database()
        print("🔒 Database connection pool closed.")


async def main() -> None:
    """CLI entrypoint for data seeding."""
    parser = argparse.ArgumentParser(
        description="Seed financial test data for AI Agent analysis."
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Database connection URL (defaults to Settings.DATABASE_URL).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Reset and recreate database tables before seeding.",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip running the AI Executive Summary use case.",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="2026-03",
        help="Fiscal period for anomaly evaluation (default: '2026-03').",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="pt-br",
        choices=["pt-br", "en-us"],
        help="Language locale for AI summary (default: 'pt-br').",
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Enable SQL logging.",
    )
    args = parser.parse_args()

    await run_seed_and_analysis(
        database_url=args.database_url,
        clean=args.clean,
        no_ai=args.no_ai,
        period=args.period,
        lang=args.lang,
        echo=args.echo,
    )


if __name__ == "__main__":
    asyncio.run(main())
