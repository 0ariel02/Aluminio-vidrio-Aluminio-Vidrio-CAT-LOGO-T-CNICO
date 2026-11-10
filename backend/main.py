import os
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from backend.database import engine, get_db, Base
from backend.models import Tenant, User, ProfileBrand, GlassType, Project, Quote, UserRole
from backend.schemas import (
    TenantBase, TenantCreate, TenantOut, UserRegister, UserLogin, UserOut, TokenResponse,
    CalculateRequest, CalculateResponse, OptimizationRequest, OptimizationResponse
)
from backend.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_authenticated_user, require_roles
)
from backend.engine.calculator import calcular_despiece, CATALOGO_PRODUCTOS
from backend.engine.optimizer import optimize_linear_cuts
from backend.reports import generate_quote_pdf

# Inicializar tablas en base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aluminio & Vidrio API - Sistema Paramétrico Multi-tenant",
    description="Backend Headless para cálculo técnico, optimización de cortes 1D, roles RBAC y gestión multi-taller.",
    version="2.0.0"
)

# CORS para integración frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sembrar datos por defecto si la base está vacía
def seed_default_data():
    db = next(get_db())
    try:
        if not db.query(Tenant).first():
            tenant = Tenant(
                slug="plascencia",
                name="Carpintería de Aluminio Plascencia",
                rfc="CAPL800101XYZ",
                address="Av. Federalismo Norte 1420, Guadalajara, Jal.",
                phone="+52 33 2082 7128",
                email="cotizaciones@aluminioyvidrio.mx",
                precio_vidrio_4mm=450.0,
                precio_vidrio_6mm=620.0,
                precio_vidrio_templado_8mm=980.0,
                precio_vidrio_templado_10mm=1250.0,
                precio_aluminio_metro=180.0,
                porcentaje_herrajes=18.0,
                costo_instalacion_base=0.0
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

            # Usuarios por defecto para cada rol RBAC
            admin = User(
                tenant_id=tenant.id,
                email="admin@plascencia.com",
                hashed_password=hash_password("admin123"),
                full_name="Ariel Administrador",
                role=UserRole.ADMINISTRADOR.value
            )
            vendedor = User(
                tenant_id=tenant.id,
                email="vendedor@plascencia.com",
                hashed_password=hash_password("vendedor123"),
                full_name="Carlos Vendedor",
                role=UserRole.VENDEDOR.value
            )
            operario = User(
                tenant_id=tenant.id,
                email="operario@plascencia.com",
                hashed_password=hash_password("operario123"),
                full_name="Juan Operario Taller",
                role=UserRole.OPERARIO.value
            )
            db.add_all([admin, vendedor, operario])

            # Marcas de perfiles
            marcas = [
                ProfileBrand(
                    code="cuprum",
                    name="Cuprum Eurovent / Línea Panorama",
                    description="Perfilería comercial y residencial de alta precisión (barras de 6.10m)",
                    bar_length_mm=6100.0
                ),
                ProfileBrand(
                    code="indalum",
                    name="Indalum Nacional",
                    description="Sistemas arquitectónicos para cancelería pesada y fachadas integrales",
                    bar_length_mm=6100.0
                ),
                ProfileBrand(
                    code="eurovent",
                    name="Eurovent Classic / Premium",
                    description="Perfiles europeos con rotura de puente térmico y hermeticidad acústica",
                    bar_length_mm=6100.0
                )
            ]
            db.add_all(marcas)

            # Grosores de vidrio
            vidrios = [
                GlassType(code="4mm", name="Vidrio claro 4mm recocido", thickness_mm=4.0, is_tempered=False, base_price_m2=450.0),
                GlassType(code="6mm", name="Vidrio claro 6mm recocido", thickness_mm=6.0, is_tempered=False, base_price_m2=620.0),
                GlassType(code="templado8mm", name="Cristal templado claro 8mm c/cantos pulidos", thickness_mm=8.0, is_tempered=True, base_price_m2=980.0),
                GlassType(code="templado10mm", name="Cristal templado claro 10mm de seguridad", thickness_mm=10.0, is_tempered=True, base_price_m2=1250.0),
            ]
            db.add_all(vidrios)
            db.commit()
    finally:
        db.close()

seed_default_data()

# ==============================================================================
# AUTH & ROLES (RBAC) & TENANT ENDPOINTS
# ==============================================================================
@app.post("/api/auth/register", response_model=TokenResponse)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Buscar o crear taller (Multi-tenant)
    slug = user_in.tenant_slug or "general"
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if not tenant:
        tenant = Tenant(slug=slug, name=user_in.tenant_name or f"Taller {slug.title()}")
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este correo ya se encuentra registrado.")

    # Validar rol asignado
    valid_roles = [r.value for r in UserRole]
    role = user_in.role if user_in.role in valid_roles else UserRole.VENDEDOR.value

    user = User(
        tenant_id=tenant.id,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role, "tenant_id": tenant.id})
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            tenant_id=tenant.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            tenant_name=tenant.name
        )
    )

@app.post("/api/auth/login", response_model=TokenResponse)
def login(creds: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email, User.is_active == True).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas.")

    tenant = user.tenant
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id})
    return TokenResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            tenant_name=tenant.name if tenant else None
        )
    )

@app.get("/api/auth/me", response_model=UserOut)
def get_me(user: User = Depends(require_authenticated_user)):
    return UserOut(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        tenant_name=user.tenant.name if user.tenant else None
    )

# ==============================================================================
# MOTOR PARAMÉTRICO Y CÁLCULO
# ==============================================================================
@app.get("/api/catalogs")
def get_catalogs(db: Session = Depends(get_db)):
    """
    Retorna el catálogo unificado de modelos paramétricos, marcas de perfiles y grosores de vidrio.
    """
    brands = db.query(ProfileBrand).all()
    glass = db.query(GlassType).all()
    return {
        "products": CATALOGO_PRODUCTOS,
        "brands": [{"code": b.code, "name": b.name, "description": b.description, "bar_length_mm": b.bar_length_mm} for b in brands],
        "glass_types": [{"code": g.code, "name": g.name, "thickness_mm": g.thickness_mm, "is_tempered": g.is_tempered, "base_price_m2": g.base_price_m2} for g in glass]
    }

@app.post("/api/calculate", response_model=CalculateResponse)
def calculate_quote(req: CalculateRequest, db: Session = Depends(get_db), user: Optional[User] = Depends(get_current_user)):
    """
    Desacoplamiento: calcula matemáticamente componentes, vidrios y costos estimados en backend.
    Si el usuario está autenticado en un tenant, utiliza sus precios configurados si no se sobreescriben.
    """
    precios = {}
    if user and user.tenant:
        t = user.tenant
        precios = {
            "precio_vidrio_4mm": t.precio_vidrio_4mm,
            "precio_vidrio_6mm": t.precio_vidrio_6mm,
            "precio_vidrio_templado_8mm": t.precio_vidrio_templado_8mm,
            "precio_vidrio_templado_10mm": t.precio_vidrio_templado_10mm,
            "precio_aluminio_metro": t.precio_aluminio_metro,
            "porcentaje_herrajes": t.porcentaje_herrajes,
            "costo_instalacion": t.costo_instalacion_base
        }

    # Sobrescritura si la petición envía parámetros específicos
    if req.precio_vidrio_4mm is not None: precios["precio_vidrio_4mm"] = req.precio_vidrio_4mm
    if req.precio_vidrio_6mm is not None: precios["precio_vidrio_6mm"] = req.precio_vidrio_6mm
    if req.precio_vidrio_templado_8mm is not None: precios["precio_vidrio_templado_8mm"] = req.precio_vidrio_templado_8mm
    if req.precio_vidrio_templado_10mm is not None: precios["precio_vidrio_templado_10mm"] = req.precio_vidrio_templado_10mm
    if req.precio_aluminio_metro is not None: precios["precio_aluminio_metro"] = req.precio_aluminio_metro
    if req.porcentaje_herrajes is not None: precios["porcentaje_herrajes"] = req.porcentaje_herrajes
    if req.costo_instalacion is not None: precios["costo_instalacion"] = req.costo_instalacion

    try:
        result = calcular_despiece(req.product_key, req.width_mm, req.height_mm, precios)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

# ==============================================================================
# OPTIMIZADOR LINEAL DE PERFILES (6.10m NESTING)
# ==============================================================================
@app.post("/api/optimize", response_model=OptimizationResponse)
def optimize_cuts(req: OptimizationRequest):
    """
    Linear Packing / Nesting para barras de perfilería de aluminio de 6.10 metros.
    Minimiza desperdicio de barras para cancelería y torres.
    """
    try:
        return optimize_linear_cuts(req.pieces, req.bar_length_mm, req.blade_thickness_mm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==============================================================================
# GENERACIÓN DE REPORTES PDF Y HOJAS DE TALLER
# ==============================================================================
@app.post("/api/reports/quote-pdf")
def export_quote_pdf(
    calc_res: CalculateResponse,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    """
    Exportación de cotizaciones y hojas de corte en PDF con datos fiscales y membrete.
    """
    tenant_info = {
        "name": "Carpintería Aluminio & Vidrio Plascencia",
        "rfc": "RFC: CAPL800101XYZ",
        "address": "Av. Federalismo Norte 1420, Guadalajara, Jal.",
        "phone": "+52 33 2082 7128",
        "email": "cotizaciones@aluminioyvidrio.mx"
    }

    if user and user.tenant:
        t = user.tenant
        tenant_info["name"] = t.name
        if t.rfc: tenant_info["rfc"] = f"RFC: {t.rfc}"
        if t.address: tenant_info["address"] = t.address
        if t.phone: tenant_info["phone"] = t.phone
        if t.email: tenant_info["email"] = t.email

    pdf_bytes = generate_quote_pdf(calc_res.model_dump(), tenant_info)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cotizacion_{calc_res.product_key}.pdf"}
    )

# ==============================================================================
# CONFIGURACIÓN DE TENANT (Solo Administrador)
# ==============================================================================
@app.put("/api/tenants/current")
def update_tenant_settings(
    settings: TenantBase,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles([UserRole.ADMINISTRADOR.value]))
):
    """
    Permite al Administrador configurar costos globales, tarifas de instalación y márgenes de insumos.
    """
    tenant = admin.tenant
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado.")

    tenant.name = settings.name
    tenant.rfc = settings.rfc
    tenant.address = settings.address
    tenant.phone = settings.phone
    tenant.email = settings.email
    tenant.precio_vidrio_4mm = settings.precio_vidrio_4mm
    tenant.precio_vidrio_6mm = settings.precio_vidrio_6mm
    tenant.precio_vidrio_templado_8mm = settings.precio_vidrio_templado_8mm
    tenant.precio_vidrio_templado_10mm = settings.precio_vidrio_templado_10mm
    tenant.precio_aluminio_metro = settings.precio_aluminio_metro
    tenant.porcentaje_herrajes = settings.porcentaje_herrajes
    tenant.costo_instalacion_base = settings.costo_instalacion_base

    db.commit()
    return {"status": "success", "message": "Configuración de taller actualizada exitosamente."}

# Servir archivos estáticos del frontend
@app.get("/")
@app.get("/index.html")
def read_root():
    return FileResponse("index.html")

@app.get("/login.html")
def read_login():
    return FileResponse("login.html")
