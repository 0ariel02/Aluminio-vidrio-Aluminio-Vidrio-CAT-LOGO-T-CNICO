from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Tenant Schemas ---
class TenantBase(BaseModel):
    slug: str
    name: str
    rfc: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    precio_vidrio_4mm: float = 450.0
    precio_vidrio_6mm: float = 620.0
    precio_vidrio_templado_8mm: float = 980.0
    precio_vidrio_templado_10mm: float = 1250.0
    precio_aluminio_metro: float = 180.0
    porcentaje_herrajes: float = 18.0
    costo_instalacion_base: float = 0.0

class TenantCreate(TenantBase):
    pass

from pydantic import ConfigDict

class TenantOut(TenantBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: datetime

# --- User & Auth Schemas ---
class UserRegister(BaseModel):
    tenant_slug: Optional[str] = "plascencia"  # Taller por defecto o asignado
    tenant_name: Optional[str] = "Carpintería de Aluminio Plascencia"
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "Vendedor"  # Administrador, Vendedor, Operario

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    tenant_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# --- Calculation Engine Schemas ---
class CalculateRequest(BaseModel):
    product_key: str
    width_mm: float
    height_mm: float
    brand_code: Optional[str] = "cuprum"
    precio_vidrio_4mm: Optional[float] = None
    precio_vidrio_6mm: Optional[float] = None
    precio_vidrio_templado_8mm: Optional[float] = None
    precio_vidrio_templado_10mm: Optional[float] = None
    precio_aluminio_metro: Optional[float] = None
    porcentaje_herrajes: Optional[float] = None
    costo_instalacion: Optional[float] = None

class PerfilComponent(BaseModel):
    nombre: str
    cantidad: int
    formula: str
    corte: str
    medida: float

class PerforacionVidrio(BaseModel):
    descripcion: str
    distanciaBordeSuperior: Optional[float] = None
    distanciaBordeLateral: Optional[float] = None
    diametro: float
    desdeAbajo: Optional[bool] = False
    centroHorizontal: Optional[bool] = False
    alturaJaladera: Optional[float] = None

class VidrioComponent(BaseModel):
    nombre: str
    cantidad: int
    tipo: Optional[str] = None
    medidaAncho: Optional[float] = None
    medidaAlto: Optional[float] = None
    perforaciones: Optional[List[PerforacionVidrio]] = None

class CostosDesglose(BaseModel):
    costoAluminio: float
    costoVidrio: float
    subtotal: float
    porcentajeHerrajes: float
    costoHerrajes: float
    costoInstalacion: float
    total: float
    metrosAluminio: float
    areaVidrio: float

class CalculateResponse(BaseModel):
    product_key: str
    product_name: str
    categoria: str
    width_mm: float
    height_mm: float
    area_m2: float
    perfiles: List[PerfilComponent]
    vidrios: List[VidrioComponent]
    costos: CostosDesglose
    notas: Optional[str] = None
    esTemplado: bool = False

# --- Linear Optimizer Schemas ---
class CutPiece(BaseModel):
    label: str
    length_mm: float
    quantity: int = 1

class OptimizationRequest(BaseModel):
    bar_length_mm: float = 6100.0  # 6.10 metros estándar
    blade_thickness_mm: float = 3.5  # Kerf de disco de corte (3.5 mm)
    pieces: List[CutPiece]

class BarPattern(BaseModel):
    bar_index: int
    used_length_mm: float
    waste_length_mm: float
    waste_percent: float
    cuts: List[Dict[str, Any]]

class OptimizationResponse(BaseModel):
    total_bars_required: int
    bar_standard_length_mm: float
    blade_thickness_mm: float
    total_cut_length_mm: float
    total_stock_used_mm: float
    total_waste_mm: float
    total_waste_percent: float
    bars: List[BarPattern]
