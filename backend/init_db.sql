-- ====================================================================
-- SISTEMA DE COTIZACIÓN Y DESPIECE: ALUMINIO & VIDRIO
-- Esquema versionado de Base de Datos Relacional: motor_plascencia
-- Multi-tenant, Catálogo de Perfiles por Marcas (Indalum, Cuprum, Eurovent)
-- Grosores de Vidrio, Historial de Proyectos y Usuarios RBAC
-- ====================================================================

CREATE SCHEMA IF NOT EXISTS motor_plascencia;
SET search_path TO motor_plascencia, public;

-- Tabla de Talleres / Vidrierías (Multi-tenant)
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    rfc VARCHAR(20),
    address VARCHAR(255),
    phone VARCHAR(30),
    email VARCHAR(120),
    logo_url VARCHAR(255),
    precio_vidrio_4mm NUMERIC(10,2) DEFAULT 450.00,
    precio_vidrio_6mm NUMERIC(10,2) DEFAULT 620.00,
    precio_vidrio_templado_8mm NUMERIC(10,2) DEFAULT 980.00,
    precio_vidrio_templado_10mm NUMERIC(10,2) DEFAULT 1250.00,
    precio_aluminio_metro NUMERIC(10,2) DEFAULT 180.00,
    porcentaje_herrajes NUMERIC(5,2) DEFAULT 18.00,
    costo_instalacion_base NUMERIC(10,2) DEFAULT 0.00,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Usuarios con Autenticación RBAC (Administrador, Vendedor, Operario)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(120) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    role VARCHAR(30) DEFAULT 'Vendedor', -- 'Administrador', 'Vendedor', 'Operario'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Catálogo de Marcas de Perfiles de Aluminio (Indalum, Cuprum, Eurovent)
CREATE TABLE IF NOT EXISTS profile_brands (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    bar_length_mm NUMERIC(8,2) DEFAULT 6100.00, -- Longitud estándar de barra 6.10m
    series_catalog JSONB
);

-- Catálogo de Grosores y Tipos de Vidrio
CREATE TABLE IF NOT EXISTS glass_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    thickness_mm NUMERIC(5,2) NOT NULL,
    is_tempered BOOLEAN DEFAULT FALSE,
    base_price_m2 NUMERIC(10,2) NOT NULL
);

-- Proyectos de Cancelería y Torres
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    client_name VARCHAR(120) NOT NULL,
    client_phone VARCHAR(30),
    client_email VARCHAR(120),
    address VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cotizaciones y Despieces
CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    folio VARCHAR(50) UNIQUE NOT NULL,
    product_key VARCHAR(100) NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    brand_code VARCHAR(50) DEFAULT 'cuprum',
    width_mm NUMERIC(8,2) NOT NULL,
    height_mm NUMERIC(8,2) NOT NULL,
    area_m2 NUMERIC(8,2) NOT NULL,
    cost_aluminum NUMERIC(10,2) DEFAULT 0.00,
    cost_glass NUMERIC(10,2) DEFAULT 0.00,
    subtotal NUMERIC(10,2) DEFAULT 0.00,
    hardware_percent NUMERIC(5,2) DEFAULT 18.00,
    cost_hardware NUMERIC(10,2) DEFAULT 0.00,
    cost_installation NUMERIC(10,2) DEFAULT 0.00,
    total_cost NUMERIC(10,2) DEFAULT 0.00,
    components_detail JSONB,
    optimization_detail JSONB,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Datos semilla iniciales
INSERT INTO tenants (slug, name, rfc, address, phone, email, precio_vidrio_4mm, precio_vidrio_6mm, precio_vidrio_templado_8mm, precio_vidrio_templado_10mm, precio_aluminio_metro, porcentaje_herrajes)
VALUES
('plascencia', 'Carpintería de Aluminio Plascencia', 'CAPL800101XYZ', 'Av. Federalismo Norte 1420, Guadalajara, Jal.', '+52 33 2082 7128', 'cotizaciones@aluminioyvidrio.mx', 450.00, 620.00, 980.00, 1250.00, 180.00, 18.00)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO profile_brands (code, name, description, bar_length_mm)
VALUES
('cuprum', 'Cuprum', 'Línea Panorama y residencial alta especificación en barras de 6.10 metros', 6100.00),
('indalum', 'Indalum', 'Sistemas arquitectónicos para cancelería comercial pesada y fachadas', 6100.00),
('eurovent', 'Eurovent', 'Perfiles europeos con máxima estanqueidad acústica y térmica', 6100.00)
ON CONFLICT (code) DO NOTHING;

INSERT INTO glass_types (code, name, thickness_mm, is_tempered, base_price_m2)
VALUES
('4mm', 'Vidrio claro 4mm recocido', 4.00, FALSE, 450.00),
('6mm', 'Vidrio claro 6mm recocido', 6.00, FALSE, 620.00),
('templado8mm', 'Cristal templado claro 8mm', 8.00, TRUE, 980.00),
('templado10mm', 'Cristal templado claro 10mm', 10.00, TRUE, 1250.00)
ON CONFLICT (code) DO NOTHING;
