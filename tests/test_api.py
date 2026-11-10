import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_catalogs_endpoint():
    response = client.get("/api/catalogs")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "brands" in data
    assert "glass_types" in data
    assert any(b["code"] == "indalum" for b in data["brands"])
    assert any(b["code"] == "cuprum" for b in data["brands"])
    assert any(b["code"] == "eurovent" for b in data["brands"])

def test_calculate_endpoint():
    payload = {
        "product_key": "ventana_corrediza_estandar",
        "width_mm": 1800,
        "height_mm": 2100,
        "precio_aluminio_metro": 200.0,
        "porcentaje_herrajes": 18.0
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["product_key"] == "ventana_corrediza_estandar"
    assert data["costos"]["total"] > 0
    assert len(data["perfiles"]) > 0

def test_optimize_endpoint():
    payload = {
        "bar_length_mm": 6100.0,
        "blade_thickness_mm": 3.5,
        "pieces": [
            {"label": "Perfil A", "length_mm": 1500, "quantity": 4},
            {"label": "Perfil B", "length_mm": 1900, "quantity": 2}
        ]
    }
    response = client.post("/api/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_bars_required"] >= 2
    assert "bars" in data

def test_auth_login_admin():
    response = client.post("/api/auth/login", json={
        "email": "admin@plascencia.com",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "Administrador"

def test_auth_login_vendedor():
    response = client.post("/api/auth/login", json={
        "email": "vendedor@plascencia.com",
        "password": "vendedor123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "Vendedor"

def test_auth_login_operario():
    response = client.post("/api/auth/login", json={
        "email": "operario@plascencia.com",
        "password": "operario123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "Operario"

def test_auth_register_new_tenant():
    new_email = "nuevo_taller@vidrieria.com"
    response = client.post("/api/auth/register", json={
        "tenant_slug": "taller-guadalajara",
        "tenant_name": "Vidrios & Aluminios Guadalajara",
        "email": new_email,
        "password": "segurapassword123",
        "full_name": "Ingeniero Roberto",
        "role": "Administrador"
    })
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert data["user"]["tenant_name"] == "Vidrios & Aluminios Guadalajara"

def test_export_pdf_report():
    calc_res = client.post("/api/calculate", json={
        "product_key": "ventana_corrediza_estandar",
        "width_mm": 1500,
        "height_mm": 2000
    }).json()

    pdf_resp = client.post("/api/reports/quote-pdf", json=calc_res)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000
    # PDF signature "%PDF-"
    assert pdf_resp.content.startswith(b"%PDF-")
