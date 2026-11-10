from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.database import Base

class UserRole(str, Enum):
    ADMINISTRADOR = "Administrador"
    VENDEDOR = "Vendedor"
    OPERARIO = "Operario"

class Tenant(Base):
    """
    Representa un taller, vidriería o instalador suscrito (Multi-tenant).
    Aísla catálogos de precios, márgenes de utilidad y datos fiscales.
    """
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    rfc = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(120), nullable=True)
    logo_url = Column(String(255), nullable=True)

    # Configuración de márgenes y costos por defecto del taller
    precio_vidrio_4mm = Column(Float, default=450.0)
    precio_vidrio_6mm = Column(Float, default=620.0)
    precio_vidrio_templado_8mm = Column(Float, default=980.0)
    precio_vidrio_templado_10mm = Column(Float, default=1250.0)
    precio_aluminio_metro = Column(Float, default=180.0)
    porcentaje_herrajes = Column(Float, default=18.0)  # Margen típico del 18% de herrajes
    costo_instalacion_base = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="tenant", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """
    Usuario del sistema con RBAC (Administrador, Vendedor, Operario).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(30), default=UserRole.VENDEDOR.value)  # Administrador, Vendedor, Operario
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")
    quotes = relationship("Quote", back_populates="user")


class ProfileBrand(Base):
    """
    Catálogo de perfiles por marcas (Indalum, Cuprum, Eurovent, etc.)
    """
    __tablename__ = "profile_brands"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # indalum, cuprum, eurovent
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    bar_length_mm = Column(Float, default=6100.0)  # Barra estándar 6.10m
    series_catalog = Column(JSON, nullable=True)  # Detalles técnicos de series e inercia


class GlassType(Base):
    """
    Catálogo de grosores y tipos de vidrio (4mm, 6mm, templados 8mm/10mm, etc.)
    """
    __tablename__ = "glass_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # 4mm, 6mm, templado8mm, templado10mm
    name = Column(String(100), nullable=False)
    thickness_mm = Column(Float, nullable=False)
    is_tempered = Column(Boolean, default=False)
    base_price_m2 = Column(Float, nullable=False)


class Project(Base):
    """
    Proyectos para agrupar múltiples canceles, ventanas y torres de cancelería.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(150), nullable=False)
    client_name = Column(String(120), nullable=False)
    client_phone = Column(String(30), nullable=True)
    client_email = Column(String(120), nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="projects")
    quotes = relationship("Quote", back_populates="project")


class Quote(Base):
    """
    Cotizaciones técnicas y comerciales generadas para clientes.
    """
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    folio = Column(String(50), unique=True, index=True, nullable=False)
    product_key = Column(String(100), nullable=False)
    product_name = Column(String(150), nullable=False)
    brand_code = Column(String(50), default="cuprum")

    width_mm = Column(Float, nullable=False)
    height_mm = Column(Float, nullable=False)
    area_m2 = Column(Float, nullable=False)

    cost_aluminum = Column(Float, default=0.0)
    cost_glass = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    hardware_percent = Column(Float, default=18.0)
    cost_hardware = Column(Float, default=0.0)
    cost_installation = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    # Detalle de componentes y despiece calculado (JSON)
    components_detail = Column(JSON, nullable=True)
    # Resultados del optimizador de barras de 6.10m (JSON)
    optimization_detail = Column(JSON, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="quotes")
    user = relationship("User", back_populates="quotes")
    project = relationship("Project", back_populates="quotes")
