from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    AUDITOR = "auditor"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(String(100), primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)

    hashed_password = Column(String(255), nullable=False)

    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Profile
    phone = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)

    # Permissions (JSON array of permission strings)
    permissions = Column(JSON, default=[])

    # Audit
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Metadata
    metadata = Column(JSON, default={})

    # Relationships
    devices = relationship("Device", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(String(100), nullable=True, index=True)

    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)

    details = Column(JSON, default={})

    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    status = Column(String(50), default="success")  # success, failure
    error_message = Column(String(500), nullable=True)

    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])
