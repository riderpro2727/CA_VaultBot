"""
CA Vault Bot - SQLAlchemy ORM Models
Complete normalized schema for all entities.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class FileCategory(str, enum.Enum):
    CA_FOUNDATION = "ca_foundation"
    CA_INTERMEDIATE = "ca_intermediate"
    CA_FINAL = "ca_final"
    CLASS_11 = "class_11"
    CLASS_12 = "class_12"
    COMMERCE = "commerce"
    ECONOMICS = "economics"
    ACCOUNTS = "accounts"
    BUSINESS_STUDIES = "business_studies"
    TAXATION = "taxation"
    AUDIT = "audit"
    LAW = "law"
    GENERAL = "general"
    UNCATEGORIZED = "uncategorized"


class FileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    PPT = "ppt"
    PPTX = "pptx"
    ZIP = "zip"
    RAR = "rar"
    MP4 = "mp4"
    MKV = "mkv"
    AVI = "avi"
    MP3 = "mp3"
    XLSX = "xlsx"
    XLS = "xls"
    JPEG = "jpeg"
    PNG = "png"
    TXT = "txt"
    OTHER = "other"


# ── Users ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    search_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    favorites_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    activity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    join_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    registration_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    searches: Mapped[List["SearchHistory"]] = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    analytics: Mapped[List["UserAnalytics"]] = relationship("UserAnalytics", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} name={self.name!r}>"


# ── Google Drive Sources ───────────────────────────────────────────────────────

class DriveSource(Base):
    __tablename__ = "drive_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drive_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_shared_drive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    added_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_scanned: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    files: Mapped[List["DriveFile"]] = relationship("DriveFile", back_populates="drive_source")

    def __repr__(self) -> str:
        return f"<DriveSource id={self.drive_id} name={self.name!r}>"


# ── Drive Files (Index) ────────────────────────────────────────────────────────

class DriveFile(Base):
    __tablename__ = "drive_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    drive_source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("drive_sources.id"), nullable=True)
    file_name: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_name_lower: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    extension: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType), default=FileType.OTHER, nullable=False, index=True)
    category: Mapped[FileCategory] = mapped_column(Enum(FileCategory), default=FileCategory.UNCATEGORIZED, nullable=False, index=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_drive_url: Mapped[str] = mapped_column(Text, nullable=False)
    parent_folder_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    parent_folder_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    drive_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    created_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    modified_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_verified: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("drive_files.id"), nullable=True)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    drive_source: Mapped[Optional["DriveSource"]] = relationship("DriveSource", back_populates="files")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="file")

    __table_args__ = (
        Index("ix_drive_files_search", "file_name_lower", "category", "file_type", "is_available"),
        Index("ix_drive_files_popularity", "popularity_score", "click_count"),
        Index("ix_drive_files_modified", "modified_time"),
    )

    def __repr__(self) -> str:
        return f"<DriveFile id={self.file_id} name={self.file_name!r}>"


# ── Categories ────────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    emoji: Mapped[str] = mapped_column(String(10), default="📁", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Category key={self.key!r} name={self.display_name!r}>"


# ── Search History ────────────────────────────────────────────────────────────

class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category_filter: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    searched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="searches")

    __table_args__ = (
        Index("ix_search_history_user_time", "user_id", "searched_at"),
    )


# ── Favorites ─────────────────────────────────────────────────────────────────

class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_id: Mapped[int] = mapped_column(Integer, ForeignKey("drive_files.id"), nullable=False, index=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    file: Mapped["DriveFile"] = relationship("DriveFile", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("user_id", "file_id", name="uq_user_file_favorite"),
    )


# ── Analytics ─────────────────────────────────────────────────────────────────

class UserAnalytics(Base):
    __tablename__ = "user_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    query: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="analytics")

    __table_args__ = (
        Index("ix_analytics_event_time", "event_type", "occurred_at"),
    )


# ── Global Analytics / Search Keywords ───────────────────────────────────────

class SearchKeyword(Base):
    __tablename__ = "search_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    search_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_searched: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


# ── Index Run Log ──────────────────────────────────────────────────────────────

class IndexRun(Base):
    __tablename__ = "index_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    drive_source_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("drive_sources.id"), nullable=True)
    files_scanned: Mapped[int] = mapped_column(Integer, default=0)
    files_added: Mapped[int] = mapped_column(Integer, default=0)
    files_removed: Mapped[int] = mapped_column(Integer, default=0)
    files_updated: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="running")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
