"""SQLAlchemy ORM models for Budgeting Bounded Context."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.base import Base


class CostCenterModel(Base):
    """SQLAlchemy model representing an organizational cost center."""

    __tablename__ = "cost_centers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("cost_centers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent: Mapped[CostCenterModel | None] = relationship(
        "CostCenterModel",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list[CostCenterModel]] = relationship(
        "CostCenterModel",
        back_populates="parent",
    )
    budgets: Mapped[list[BudgetTargetModel]] = relationship(
        "BudgetTargetModel",
        back_populates="cost_center",
        cascade="all, delete-orphan",
    )


class BudgetTargetModel(Base):
    """SQLAlchemy model representing planned budget target commitments."""

    __tablename__ = "budget_targets"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    cost_center_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("cost_centers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    cost_center: Mapped[CostCenterModel] = relationship(
        "CostCenterModel",
        back_populates="budgets",
    )
