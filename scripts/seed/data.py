"""Seed dataset specifications and configuration models for enterprise finance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostCenterSpec:
    """Specification for cost center seeding."""

    code: str
    name: str
    parent_code: str | None = None


@dataclass(frozen=True)
class AccountSpec:
    """Specification for chart of accounts seeding."""

    code: str
    name: str
    description: str


@dataclass(frozen=True)
class BudgetSpec:
    """Specification for budget targets seeding."""

    cost_center_code: str
    period_str: str
    amount: str


@dataclass(frozen=True)
class SupplierSpec:
    """Specification for vendor supplier seeding."""

    name: str
    tax_id: str


COST_CENTER_SPECS: list[CostCenterSpec] = [
    CostCenterSpec("1.0", "Executive Board & Corporate", None),
    CostCenterSpec("1.1", "Information Technology", "1.0"),
    CostCenterSpec("1.1.1", "Cloud Infrastructure", "1.1"),
    CostCenterSpec("1.1.2", "Software Engineering", "1.1"),
    CostCenterSpec("1.2", "Operations & Logistics", "1.0"),
    CostCenterSpec("1.3", "Marketing & Growth", "1.0"),
]

ACCOUNT_SPECS: list[AccountSpec] = [
    AccountSpec(
        "3.1.01",
        "Infraestrutura Cloud & Hosting",
        "Serviços de computação, armazenamento e instâncias em nuvem",
    ),
    AccountSpec(
        "3.1.02",
        "Licenciamento de Software & Ferramentas SaaS",
        "Licenças de software para engenharia, ferramentas CI/CD e SaaS",
    ),
    AccountSpec(
        "3.1.03",
        "Consultoria Técnica & Serviços Especializados",
        "Serviços profissionais e consultoria especializada de TI",
    ),
    AccountSpec(
        "3.2.01",
        "Serviços de Logística e Fretes",
        "Distribuição regional, frota dedicada e fretes operacionais",
    ),
    AccountSpec(
        "3.3.01",
        "Publicidade, Campanhas e Mídia",
        "Veiculação de mídia digital e publicidade de crescimento",
    ),
]

SUPPLIER_SPECS: list[SupplierSpec] = [
    SupplierSpec("Amazon Web Services Inc.", "12.345.678/0001-90"),
    SupplierSpec("Global Logistics Partners", "98.765.432/0001-10"),
    SupplierSpec("Acme Creative Studio", "44.555.666/0001-22"),
    SupplierSpec("TechConsult Architecture Partners", "55.666.777/0001-33"),
]
