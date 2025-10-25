from datetime import date
from typing import List, Optional

from sqlalchemy import (
    ForeignKey,
    UniqueConstraint,
    Numeric,
    String,
    Date,
    Boolean,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class Fundraise(Base):
    __tablename__ = "fundraise"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    raised_money: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    target_money: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    finished: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    contributors: Mapped[List["UserFundraise"]] = relationship(
        back_populates="fundraise",
        cascade="all, delete-orphan"
    )
    leaderboards: Mapped[List["Leaderboard"]] = relationship(
        back_populates="fundraise",
        cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), nullable=False, uniqTrue)
    mail: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    pass_: Mapped[str] = mapped_column("pass", String(255), nullable=False)
    total_spent: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    companies: Mapped[List["UserCompanyLink"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    donations: Mapped[List["UserFundraise"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    leaderboard_rows: Mapped[List["Leaderboard"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Company(Base):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    users: Mapped[List["UserCompanyLink"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan"
    )


class UserCompanyLink(Base):
    __tablename__ = "user_company_link"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_user_company"),
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("company.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_points: Mapped[Optional[int]] = mapped_column(nullable=True)

    company: Mapped["Company"] = relationship(back_populates="users")
    user: Mapped["User"] = relationship(back_populates="companies")


class UserFundraise(Base):
    __tablename__ = "user_fundraise"
    __table_args__ = (
        UniqueConstraint("user_id", "fundraise_id", name="uq_user_fundraise"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    fundraise_id: Mapped[int] = mapped_column(
        ForeignKey("fundraise.id", ondelete="CASCADE"),
        nullable=False
    )
    money_summary: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    user: Mapped["User"] = relationship(back_populates="donations")
    fundraise: Mapped["Fundraise"] = relationship(back_populates="contributors")


class Leaderboard(Base):
    __tablename__ = "leaderboard"
    __table_args__ = (
        UniqueConstraint("user_id", "fundraise_id", name="uq_leaderboard_user_fundraise"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    fundraise_id: Mapped[int] = mapped_column(
        ForeignKey("fundraise.id", ondelete="CASCADE"),
        nullable=False
    )
    total_spent: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    user: Mapped["User"] = relationship(back_populates="leaderboard_rows")
    fundraise: Mapped["Fundraise"] = relationship(back_populates="leaderboards")
