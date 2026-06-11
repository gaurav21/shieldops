"""Database models for ShieldOps enterprise backend."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator, CHAR


class PortableUUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise stores as CHAR(32).
    Works correctly on both PostgreSQL and SQLite.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_PortableUUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        else:
            if isinstance(value, uuid.UUID):
                return value.hex
            return uuid.UUID(value).hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)

from .database import Base


# Enums
class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class VulnStatus(str, Enum):
    DETECTED = "detected"
    TRIAGING = "triaging"
    REMEDIATING = "remediating"
    FIXED = "fixed"
    BLOCKED = "blocked"
    IGNORED = "ignored"


class VulnSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class UserRole(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


# Models
class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    github_org_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    installation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    plan: Mapped[PlanType] = mapped_column(
        SQLEnum(PlanType), nullable=False, default=PlanType.FREE
    )
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    repositories: Mapped[List["Repository"]] = relationship(
        "Repository", back_populates="organization"
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="organization"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="organization"
    )


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("organizations.id"), nullable=False
    )
    github_repo_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), nullable=False, default="main")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scan_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=lambda: {
        "scan_types": ["pip-audit", "npm-audit", "trivy", "semgrep"],
        "schedule": "daily",
        "auto_fix": True,
        "excluded_paths": [],
        "severity_threshold": "medium"
    })
    policy_overrides: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="repositories"
    )
    vulnerabilities: Mapped[List["Vulnerability"]] = relationship(
        "Vulnerability", back_populates="repository"
    )
    remediation_sessions: Mapped[List["RemediationSession"]] = relationship(
        "RemediationSession", back_populates="repository"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="repository"
    )


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    repo_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("repositories.id"), nullable=False
    )
    cve_id: Mapped[Optional[str]] = mapped_column(String(50))
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_version: Mapped[Optional[str]] = mapped_column(String(100))
    fixed_version: Mapped[Optional[str]] = mapped_column(String(100))
    severity: Mapped[VulnSeverity] = mapped_column(
        SQLEnum(VulnSeverity), nullable=False
    )
    vuln_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reachable: Mapped[Optional[bool]] = mapped_column(Boolean)
    status: Mapped[VulnStatus] = mapped_column(
        SQLEnum(VulnStatus), nullable=False, default=VulnStatus.DETECTED
    )
    github_issue_number: Mapped[Optional[int]] = mapped_column(Integer)
    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(
        "Repository", back_populates="vulnerabilities"
    )
    remediation_sessions: Mapped[List["RemediationSession"]] = relationship(
        "RemediationSession", back_populates="vulnerability"
    )


class RemediationSession(Base):
    __tablename__ = "remediation_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    vuln_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("vulnerabilities.id"), nullable=False
    )
    repo_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("repositories.id"), nullable=False
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, default="devin")
    agent_session_id: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus), nullable=False, default=SessionStatus.PENDING
    )
    prompt: Mapped[Optional[str]] = mapped_column(Text)
    structured_output: Mapped[Optional[dict]] = mapped_column(JSON)
    policy_decision: Mapped[Optional[str]] = mapped_column(String(100))
    policy_reason: Mapped[Optional[str]] = mapped_column(Text)
    pr_url: Mapped[Optional[str]] = mapped_column(String(500))
    pr_number: Mapped[Optional[int]] = mapped_column(Integer)
    evidence_bundle: Mapped[Optional[str]] = mapped_column(Text)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    acu_cost: Mapped[Optional[float]] = mapped_column()
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    vulnerability: Mapped["Vulnerability"] = relationship(
        "Vulnerability", back_populates="remediation_sessions"
    )
    repository: Mapped["Repository"] = relationship(
        "Repository", back_populates="remediation_sessions"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    github_user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    login: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("organizations.id"), nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="users"
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("organizations.id"), nullable=False
    )
    repo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PortableUUID(), ForeignKey("repositories.id")
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="audit_logs"
    )
    repository: Mapped[Optional["Repository"]] = relationship(
        "Repository", back_populates="audit_logs"
    )