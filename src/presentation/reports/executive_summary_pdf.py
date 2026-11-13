"""PDF report generator for Strategic Intelligence executive summaries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from fpdf import FPDF
from fpdf.enums import Align

from src.intelligence.application.dto import ExecutiveSummaryDTO
from src.shared.domain.value_objects import SupportedLanguage

I18N_LABELS: dict[SupportedLanguage, dict[str, Any]] = {
    SupportedLanguage.PT_BR: {
        "header_title": (
            "INDICADORES ESTRATÉGICOS IA  |  RELATÓRIO DO SUMÁRIO EXECUTIVO"
        ),
        "header_period": "PERÍODO: {period}",
        "footer_confidential": "Confidencial - Governança Corporativa Interna",
        "footer_page": "Página {page}/{nb}",
        "doc_title": "Sumário Executivo de Inteligência Financeira",
        "meta_fiscal_period": "Período Fiscal",
        "meta_generated_on": "Gerado em",
        "meta_engine": "Motor",
        "badge_prefix": "STATUS DE SAÚDE FINANCEIRA",
        "fallback_banner": (
            "AVISO: Modelo de IA offline ou tempo limite excedido. "
            "Relatório sintetizado via heurísticas determinísticas."
        ),
        "kpi_budgeted": "Total Orçado",
        "kpi_actual": "Total Realizado",
        "kpi_variance": "Variação",
        "kpi_execution_rate": "Taxa de Execução",
        "sec_narrative": "1. Síntese Executiva & Avaliação",
        "sec_root_causes": "2. Principais Direcionadores de Custo & Causas-Raiz",
        "sec_recommendations": "3. Ações Estratégicas Recomendadas",
        "sec_table": "4. Desempenho Orçamentário por Centro de Custo",
        "col_code": "Código",
        "col_budgeted": "Orçado",
        "col_actual": "Realizado",
        "col_variance": "Variação",
        "col_exec_pct": "Exec %",
        "col_status": "Status",
        "sec_anomalies": "5. Auditoria & Detecção de Anomalias de Rateio",
        "no_anomalies": (
            "Nenhum salto anômalo de rateio ou padrão de descarte orçamentário "
            "detectado neste período."
        ),
        "col_severity": "Severidade",
        "col_anomaly_type": "Tipo de Anomalia",
        "col_description": "Descrição",
        "status_labels": {
            "CRITICAL": "CRÍTICO",
            "CRITICAL_OVERRUN": "ESTOURO CRÍTICO",
            "WARNING": "ATENÇÃO",
            "NORMAL": "NORMAL",
            "HEALTHY": "SAUDÁVEL",
            "CONCERNING": "ATENÇÃO",
            "INDISPONÍVEL (FALLBACK DE IA)": "INDISPONÍVEL (FALLBACK DE IA)",
            "UNAVAILABLE (AI FALLBACK)": "INDISPONÍVEL (FALLBACK DE IA)",
        },
    },
    SupportedLanguage.EN_US: {
        "header_title": "STRATEGIC INDICATORS AI  |  EXECUTIVE BRIEFING REPORT",
        "header_period": "PERIOD: {period}",
        "footer_confidential": "Confidential - Internal Corporate Governance",
        "footer_page": "Page {page}/{nb}",
        "doc_title": "Executive Financial Intelligence Briefing",
        "meta_fiscal_period": "Fiscal Period",
        "meta_generated_on": "Generated on",
        "meta_engine": "Engine",
        "badge_prefix": "FINANCIAL HEALTH STATUS",
        "fallback_banner": (
            "ADVISORY: AI model was offline or timed out. "
            "Report synthesized using deterministic financial heuristics."
        ),
        "kpi_budgeted": "Total Budgeted",
        "kpi_actual": "Total Actual",
        "kpi_variance": "Variance",
        "kpi_execution_rate": "Execution Rate",
        "sec_narrative": "1. Executive Summary & Assessment",
        "sec_root_causes": "2. Key Cost Drivers & Root Causes",
        "sec_recommendations": "3. Recommended Strategic Actions",
        "sec_table": "4. Cost Center Budget Performance",
        "col_code": "Code",
        "col_budgeted": "Budgeted",
        "col_actual": "Actual",
        "col_variance": "Variance",
        "col_exec_pct": "Exec %",
        "col_status": "Status",
        "sec_anomalies": "5. Cost Allocation Anomaly Detection",
        "no_anomalies": (
            "No anomalous rateio shifts or budget dumping patterns "
            "detected for this period."
        ),
        "col_severity": "Severity",
        "col_anomaly_type": "Anomaly Type",
        "col_description": "Description",
        "status_labels": {
            "CRITICAL": "CRITICAL",
            "CRITICAL_OVERRUN": "CRITICAL OVERRUN",
            "WARNING": "WARNING",
            "NORMAL": "NORMAL",
            "HEALTHY": "HEALTHY",
            "CONCERNING": "CONCERNING",
            "INDISPONÍVEL (FALLBACK DE IA)": "UNAVAILABLE (AI FALLBACK)",
            "UNAVAILABLE (AI FALLBACK)": "UNAVAILABLE (AI FALLBACK)",
        },
    },
}


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

    def __init__(
        self,
        period_str: str,
        status_str: str,
        language: SupportedLanguage = SupportedLanguage.PT_BR,
    ) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.period_str = period_str
        self.status_str = status_str
        self.language = language
        self.set_auto_page_break(auto=True, margin=18)
        self.alias_nb_pages()

    def header(self) -> None:
        """Render running document top banner."""
        labels = I18N_LABELS[self.language]
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 116, 139)  # Slate
        self.cell(
            0,
            6,
            labels["header_title"],
            align="L",
        )
        self.cell(
            0,
            6,
            labels["header_period"].format(period=self.period_str),
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
        labels = I18N_LABELS[self.language]
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
            labels["footer_confidential"],
            align="L",
        )
        self.cell(
            0,
            6,
            labels["footer_page"].format(page=self.page_no(), nb="{nb}"),
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

    def build(
        self,
        dto: ExecutiveSummaryDTO,
        language: SupportedLanguage | None = None,
    ) -> bytes:
        """Generate PDF report byte array from executive summary DTO.

        Args:
            dto: The synthesized executive summary transfer object.
            language: Desired document language (defaults to dto.language).

        Returns:
            bytes: The formatted binary PDF content.
        """
        lang = language or dto.language
        labels = I18N_LABELS[lang]
        period_str = str(dto.period)
        status_str = dto.financial_health_status.upper()

        pdf = _ExecutiveReportPDF(
            period_str=period_str,
            status_str=status_str,
            language=lang,
        )
        pdf.add_page()

        self._render_title_and_badge(pdf, dto, labels)
        if dto.is_fallback:
            self._render_fallback_banner(pdf, labels)

        self._render_kpi_cards(pdf, dto, labels)
        self._render_narrative_section(pdf, dto, labels)
        self._render_root_causes_and_recommendations(pdf, dto, labels)
        self._render_indicators_table(pdf, dto, labels)
        self._render_anomalies_section(pdf, dto, labels)

        return bytes(pdf.output())

    def _render_title_and_badge(
        self,
        pdf: _ExecutiveReportPDF,
        dto: ExecutiveSummaryDTO,
        labels: dict[str, Any],
    ) -> None:
        """Render top title, generation metadata, and health status badge."""
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*self.PRIMARY)
        pdf.cell(
            pdf.epw,
            8,
            labels["doc_title"],
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*self.SECONDARY)
        gen_time = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        meta_line = (
            f"{labels['meta_fiscal_period']}: {dto.period}  |  "
            f"{labels['meta_generated_on']}: {gen_time}  |  "
            f"{labels['meta_engine']}: {dto.ai_provider.upper()}"
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

        status_text = labels["status_labels"].get(status, status.replace("_", " "))
        badge_text = f"{labels['badge_prefix']}: {status_text}"
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

    def _render_fallback_banner(
        self,
        pdf: _ExecutiveReportPDF,
        labels: dict[str, Any],
    ) -> None:
        """Render notice banner if AI provider operated in offline fallback mode."""
        pdf.set_fill_color(254, 242, 242)
        pdf.set_draw_color(248, 113, 113)
        pdf.set_text_color(153, 27, 27)
        pdf.set_font("Helvetica", "B", 8)
        advisory_msg = labels["fallback_banner"]
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
        self,
        pdf: _ExecutiveReportPDF,
        dto: ExecutiveSummaryDTO,
        labels: dict[str, Any],
    ) -> None:
        """Render top KPI highlight cards."""
        ind = dto.indicators_summary
        currency = ind.currency

        kpis = [
            (labels["kpi_budgeted"], f"{currency} {ind.total_budgeted:,.2f}"),
            (labels["kpi_actual"], f"{currency} {ind.total_actual:,.2f}"),
            (labels["kpi_variance"], f"{currency} {ind.total_variance:,.2f}"),
            (labels["kpi_execution_rate"], f"{ind.total_execution_rate:.1f}%"),
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
        self,
        pdf: _ExecutiveReportPDF,
        dto: ExecutiveSummaryDTO,
        labels: dict[str, Any],
    ) -> None:
        """Render executive narrative summary."""
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*self.PRIMARY)
        pdf.cell(
            pdf.epw,
            6,
            labels["sec_narrative"],
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
        self,
        pdf: _ExecutiveReportPDF,
        dto: ExecutiveSummaryDTO,
        labels: dict[str, Any],
    ) -> None:
        """Render key root causes and strategic action recommendations."""
        if dto.root_causes:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*self.PRIMARY)
            pdf.cell(
                pdf.epw,
                6,
                labels["sec_root_causes"],
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
                labels["sec_recommendations"],
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
        self,
        pdf: _ExecutiveReportPDF,
        dto: ExecutiveSummaryDTO,
        labels: dict[str, Any],
    ) -> None:
        """Render consolidated cost center indicators in a clean tabular grid."""
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*self.PRIMARY)
        pdf.cell(
            pdf.epw,
            6,
            labels["sec_table"],
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
            hdr.cell(labels["col_code"])
            hdr.cell(labels["col_budgeted"])
            hdr.cell(labels["col_actual"])
            hdr.cell(labels["col_variance"])
            hdr.cell(labels["col_exec_pct"])
            hdr.cell(labels["col_status"])

            # Data Rows
            pdf.set_font("Helvetica", "", 8)
            for ind in dto.indicators_summary.indicators:
                row = table.row()
                row.cell(ind.cost_center_code)
                row.cell(f"{ind.budgeted_amount:,.2f}")
                row.cell(f"{ind.actual_amount:,.2f}")
                row.cell(f"{ind.variance_amount:,.2f}")
                row.cell(f"{ind.execution_rate:.1f}%")
                status_label = labels["status_labels"].get(ind.status, ind.status)
                row.cell(status_label)

        pdf.ln(6)

    def _render_anomalies_section(
        self,
        pdf: _ExecutiveReportPDF,
        dto: ExecutiveSummaryDTO,
        labels: dict[str, Any],
    ) -> None:
        """Render detected allocation anomalies section and table."""
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*self.PRIMARY)
        pdf.cell(
            pdf.epw,
            6,
            labels["sec_anomalies"],
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        if not dto.anomalies:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*self.SECONDARY)
            no_anomalies_msg = labels["no_anomalies"]
            pdf.cell(pdf.epw, 5, no_anomalies_msg, new_x="LMARGIN", new_y="NEXT")
            return

        col_widths = (25, 50, 105)
        with pdf.table(
            col_widths=col_widths,
            text_align=(Align.C, Align.L, Align.L),
        ) as table:
            pdf.set_font("Helvetica", "B", 8)
            hdr = table.row()
            hdr.cell(labels["col_severity"])
            hdr.cell(labels["col_anomaly_type"])
            hdr.cell(labels["col_description"])

            pdf.set_font("Helvetica", "", 8)
            for a in dto.anomalies:
                row = table.row()
                row.cell(a.severity.value)
                row.cell(a.anomaly_type.value)
                row.cell(_clean_text(a.description))
