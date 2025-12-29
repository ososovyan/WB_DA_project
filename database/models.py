from datetime import datetime
from typing import List, Optional, Any, Dict

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Region(Base):
    __tablename__ = "regions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    iso2_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    countries: Mapped[List["Country"]] = relationship(
        "Country",
        back_populates="region",
        cascade="all, delete-orphan"
    )

class AdminRegion(Base):
    __tablename__ = "admin_regions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    iso2_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    countries: Mapped[List["Country"]] = relationship(
        "Country",
        back_populates="admin_region"
    )

class LendingType(Base):
    __tablename__ = "lending_types"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    iso2_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    countries: Mapped[List["Country"]] = relationship(
        "Country",
        back_populates="lending_type"
    )

class IncomeLevel(Base):
    __tablename__ = "income_levels"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    iso2_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    countries: Mapped[List["Country"]] = relationship(
        "Country",
        back_populates="income_level"
    )

class Country(Base):
    __tablename__ = "countries"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    iso2_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    capital_city: Mapped[str] = mapped_column(String(50), nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)

    region_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("regions.id", ondelete="CASCADE"), nullable=False
    )
    admin_region_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("admin_regions.id", ondelete="SET NULL"), nullable=True
    )
    income_level_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("income_levels.id", ondelete="SET NULL"), nullable=True
    )
    lending_type_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("lending_types.id", ondelete="SET NULL"), nullable=True
    )

    region: Mapped["Region"] = relationship("Region", back_populates="countries")
    admin_region: Mapped["AdminRegion"] = relationship("AdminRegion", back_populates="countries")
    income_level: Mapped["IncomeLevel"] = relationship("IncomeLevel", back_populates="countries")
    lending_type: Mapped["LendingType"] = relationship("LendingType", back_populates="countries")

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    indicators: Mapped[List["Indicator"]] = relationship(
        "Indicator",
        back_populates="source"
    )

class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(100), nullable=True)
    source_note: Mapped[str] = mapped_column(String(200), nullable=True)
    source_organisation: Mapped[str] = mapped_column(String(100), nullable=True)

    source_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("source.id", ondelete="SET NULL"), nullable=True
    )


class RawIndicatorData(Base):
    __tablename__ = "raw_indicator_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    country_id: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    value: Mapped[Optional[str]] = mapped_column(String(100))
    api_response: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Виртуальные связи (только для чтения)
    country: Mapped[Optional["Country"]] = relationship(
        "Country",
        primaryjoin="foreign(RawIndicatorData.country_id)==Country.id",
        viewonly=True
    )
    indicator: Mapped[Optional["Indicator"]] = relationship(
        "Indicator",
        primaryjoin="foreign(RawIndicatorData.indicator_id)==Indicator.id",
        viewonly=True
    )

    __table_args__ = (
        UniqueConstraint("indicator_id", "country_id", "year", name="uq_raw_data"),
    )


class NormalizedIndicatorData(Base):
    __tablename__ = "normalized_indicator_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    indicator_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    country_id: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    value_numeric: Mapped[Optional[float]] = mapped_column(Float)
    value_string: Mapped[Optional[str]] = mapped_column(String(255))
    unit: Mapped[Optional[str]] = mapped_column(String(50))

    extra_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    normalized_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    country: Mapped[Optional["Country"]] = relationship(
        "Country",
        primaryjoin="foreign(NormalizedIndicatorData.country_id)==Country.id",
        viewonly=True
    )
    indicator: Mapped[Optional["Indicator"]] = relationship(
        "Indicator",
        primaryjoin="foreign(NormalizedIndicatorData.indicator_id)==Indicator.id",
        viewonly=True
    )

    __table_args__ = (
        UniqueConstraint("indicator_code", "country_code", "year", name="uq_norm_data"),
    )