"""PDF report generator for Strategic Intelligence executive summaries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from fpdf import FPDF
from fpdf.enums import Align

from src.intelligence.application.dto import ExecutiveSummaryDTO


def _clean_text(text: str) -> str:
    """Sanitize typography and unicode characters for standard PDF fonts.

    Args:
        text: Input string possibly containing unsupported unicode characters.

    Returns:
        str: Latin-1 compatible sanitized string.
    """
    if not text:
        return ""
    replacements = {
        "\u2014": "-",  # em-dash
        "\u2013": "-",  # en-dash
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u2022": "-",  # bullet
        "\u2026": "...",  # ellipsis
        "\xa0": " ",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text.encode("latin-1", "replace").decode("latin-1")


class _ExecutiveReportPDF(FPDF):
    """Custom FPDF document styling headers and footers."""

    def __init__(self, period_str: str, status_str: str) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.period_str = period_str
        self.status_str = status_str
        self.set_auto_page_break(auto=True, margin=18)
        self.alias_nb_pages()

    def header(self) -> None:
        """Render running document top banner."""
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 116, 139)  # Slate
        self.cell(
            0,
            6,
            "STRATEGIC INDICATORS AI  |  EXECUTIVE BRIEFING REPORT",
            align="L",
        )
        self.cell(
            0,
            6,
            f"PERIOD: {self.period_str}",
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self) -> None:
        """Render running document bottom footer with page counter."""
        self.set_y(-14)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(
            0,
            6,
            "Confidential - Internal Corporate Governance",
            align="L",
        )
        self.cell(
            0,
            6,
            f"Page {self.page_no()}/{{nb}}",
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )


class ExecutiveSummaryPDFBuilder:
    """Renders an ExecutiveSummaryDTO into a styled, professional binary PDF."""

    # Color palette constants
    PRIMARY = (30, 58, 138)  # Deep Navy #1E3A8A
    SECONDARY = (71, 85, 105)  # Slate #475569
    TEXT_DARK = (15, 23, 42)  # Charcoal
    BG_LIGHT = (248, 250, 252)  # Off-white

    STATUS_COLORS: ClassVar[dict[str, dict[str, tuple[int, int, int]]]] = {
        "NORMAL": {
            "text": (22, 101, 52),
            "bg": (220, 252, 231),
            "border": (134, 239, 172),
        },
        "WARNING": {
            "text": (180, 83, 9),
            "bg": (254, 243, 199),
            "border": (252, 211, 77),
        },
        "CRITICAL_OVERRUN": {
            "text": (185, 28, 28),
            "bg": (254, 226, 226),
            "border": (252, 165, 165),
        },
    }

    def build(self, dto: ExecutiveSummaryDTO) -> bytes:
        """Generate PDF report byte array from executive summary DTO.

        Args:
            dto: The synthesized executive summary transfer object.

        Returns:
            bytes: The formatted binary PDF content.
        """
        period_str = str(dto.period)
        status_str = dto.financial_health_status.upper()

        pdf = _ExecutiveReportPDF(period_str=period_str, status_str=status_str)
        pdf.add_page()

        self._render_title_and_badge(pdf, dto)
        if dto.is_fallback:
            self._render_fallback_banner(pdf)

        self._render_kpi_cards(pdf, dto)
        self._render_narrative_section(pdf, dto)
        self._render_root_causes_and_recommendations(pdf, dto)
        self._render_indicators_table(pdf, dto)
        self._render_anomalies_section(pdf, dto)

        return bytes(pdf.output())

    def _render_title_and_badge(
        self, pdf: _ExecutiveReportPDF, dto: ExecutiveSummaryDTO
    ) -> None:
        """Render top title, generation metadata, and health status badge."""
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*self.PRIMARY)
        pdf.cell(
            pdf.epw,
            8,
            "Executive Financial Intelligence Briefing",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*self.SECONDARY)
        gen_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        meta_line = (
            f"Fiscal Period: {dto.period}  |  Generated on: {gen_time}  |  "
            f"Engine: {dto.ai_provider.upper()}"
        )
        pdf.cell(pdf.epw, 5, meta_line, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        # Health status badge
        status = dto.financial_health_status
        colors = self.STATUS_COLORS.get(status, self.STATUS_COLORS["NORMAL"])

        pdf.set_fill_color(*colors["bg"])
        pdf.set_draw_color(*colors["border"])
        pdf.set_text_color(*colors["text"])
        pdf.set_font("Helvetica", "B", 10)

        badge_text = f"FINANCIAL HEALTH STATUS: {status.replace('_', ' ')}"
        badge_w = pdf.get_string_width(badge_text) + 12
        pdf.cell(
            badge_w,
            7,
            badge_text,
            border=1,
            fill=True,
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(5)

    def _render_fallback_banner(self, pdf: _ExecutiveReportPDF) -> None:
        """Render notice banner if AI provider operated in offline fallback mode."""
        pdf.set_fill_color(254, 242, 242)
        pdf.set_draw_color(248, 113, 113)
        pdf.set_text_color(153, 27, 27)
        pdf.set_font("Helvetica", "B", 8)
        advisory_msg = (
            "ADVISORY: AI model was offline or timed out. "
            "Report synthesized using deterministic financial heuristics."
        )
        pdf.cell(
            pdf.epw,
            7,
            advisory_msg,
            border=1,
            fill=True,
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(4)

    def _render_kpi_cards(
        self, pdf: _ExecutiveReportPDF, dto: ExecutiveSummaryDTO
    ) -> None:
        """Render top KPI highlight cards."""
        ind = dto.indicators_summary
        currency = ind.currency

        kpis = [
            ("Total Budgeted", f"{currency} {ind.total_budgeted:,.2f}"),
            ("Total Actual", f"{currency} {ind.total_actual:,.2f}"),
            ("Variance", f"{currency} {ind.total_variance:,.2f}"),
            ("Execution Rate", f"{ind.total_execution_rate:.1f}%"),
        ]

        card_w = (pdf.epw - 9) / 4
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*self.SECONDARY)

        for i, (label, _) in enumerate(kpis):
            is_last = i == len(kpis) - 1
            nx = "LMARGIN" if is_last else "RIGHT"
            ny = "NEXT" if is_last else "TOP"
            pdf.cell(card_w, 4, label, align="C", new_x=nx, new_y=ny)
            if not is_last:
                pdf.cell(3, 4, "")
        pdf.ln(1)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*self.TEXT_DARK)
        pdf.set_fill_color(241, 245, 249)

        for i, (_, value) in enumerate(kpis):
            is_last = i == len(kpis) - 1
            nx = "LMARGIN" if is_last else "RIGHT"
            ny = "NEXT" if is_last else "TOP"
            pdf.cell(
                card_w, 7, value, border=1, fill=True, align="C", new_x=nx, new_y=ny
            )
            if not is_last:
                pdf.cell(3, 7, "")
        pdf.ln(8)

    def _render_narrative_section(
        self, pdf: _ExecutiveReportPDF, dto: ExecutiveSummaryDTO
    ) -> None:
        """Render executive narrative summary."""
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*self.PRIMARY)
        pdf.cell(
            pdf.epw,
            6,
            "1. Executive Summary & Assessment",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*self.TEXT_DARK)
        cleaned_summary = _clean_text(dto.executive_summary)
        pdf.multi_cell(pdf.epw, 5, cleaned_summary, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

    def _render_root_causes_and_recommendations(
        self, pdf: _ExecutiveReportPDF, dto: ExecutiveSummaryDTO
    ) -> None:
        """Render key root causes and strategic action recommendations."""
        if dto.root_causes:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*self.PRIMARY)
            pdf.cell(
                pdf.epw,
                6,
                "2. Key Cost Drivers & Root Causes",
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.ln(1)

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*self.TEXT_DARK)
            for cause in dto.root_causes:
                bullet = f"-  {_clean_text(cause)}"
                pdf.multi_cell(pdf.epw, 4.5, bullet, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        if dto.strategic_recommendations:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*self.PRIMARY)
            pdf.cell(
                pdf.epw,
                6,
                "3. Recommended Strategic Actions",
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.ln(1)

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*self.TEXT_DARK)
            for rec in dto.strategic_recommendations:
                bullet = f"-  {_clean_text(rec)}"
                pdf.multi_cell(pdf.epw, 4.5, bullet, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)

    def _render_indicators_table(
        self, pdf: _ExecutiveReportPDF, dto: ExecutiveSummaryDTO
    ) -> None:
        """Render consolidated cost center indicators in a clean tabular grid."""
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*self.PRIMARY)
        pdf.cell(
            pdf.epw,
            6,
            "4. Cost Center Budget Performance",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        col_widths = (22, 33, 33, 33, 26, 33)
        with pdf.table(
            col_widths=col_widths,
            text_align=(
                Align.C,
                Align.R,
                Align.R,
                Align.R,
                Align.R,
                Align.C,
            ),
        ) as table:
            # Header Row
            pdf.set_font("Helvetica", "B", 8)
            hdr = table.row()
            hdr.cell("Code")
            hdr.cell("Budgeted")
            hdr.cell("Actual")
            hdr.cell("Variance")
            hdr.cell("Exec %")
            hdr.cell("Status")

            # Data Rows
            pdf.set_font("Helvetica", "", 8)
            for ind in dto.indicators_summary.indicators:
                row = table.row()
                row.cell(ind.cost_center_code)
                row.cell(f"{ind.budgeted_amount:,.2f}")
                row.cell(f"{ind.actual_amount:,.2f}")
                row.cell(f"{ind.variance_amount:,.2f}")
                row.cell(f"{ind.execution_rate:.1f}%")
                row.cell(ind.status)

        pdf.ln(6)

    def _render_anomalies_section(
        self, pdf: _ExecutiveReportPDF, dto: ExecutiveSummaryDTO
    ) -> None:
        """Render detected allocation anomalies section and table."""
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*self.PRIMARY)
        pdf.cell(
            pdf.epw,
            6,
            "5. Cost Allocation Anomaly Detection",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        if not dto.anomalies:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*self.SECONDARY)
            no_anomalies_msg = (
                "No anomalous rateio shifts or budget dumping patterns "
                "detected for this period."
            )
            pdf.cell(pdf.epw, 5, no_anomalies_msg, new_x="LMARGIN", new_y="NEXT")
            return

        col_widths = (25, 50, 105)
        with pdf.table(
            col_widths=col_widths,
            text_align=(Align.C, Align.L, Align.L),
        ) as table:
            pdf.set_font("Helvetica", "B", 8)
            hdr = table.row()
            hdr.cell("Severity")
            hdr.cell("Anomaly Type")
            hdr.cell("Description")

            pdf.set_font("Helvetica", "", 8)
            for a in dto.anomalies:
                row = table.row()
                row.cell(a.severity.value)
                row.cell(a.anomaly_type.value)
                row.cell(_clean_text(a.description))
