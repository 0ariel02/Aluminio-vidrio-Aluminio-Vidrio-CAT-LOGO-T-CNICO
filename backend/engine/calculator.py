import math
import re
from typing import Dict, Any, List, Optional
from backend.schemas import CalculateResponse, PerfilComponent, VidrioComponent, PerforacionVidrio, CostosDesglose

# Catálogo maestro de productos y fórmulas de despiece
CATALOGO_PRODUCTOS = {
    "ventana_corrediza_estandar": {
        "nombre": "Ventana corrediza estándar",
        "categoria": "ventanas",
        "icono": "🪟",
        "tipoVidrio": "4mm",
        "perfiles": [
            { "nombre": "Riel / Jamba cabezal", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Jambas verticales", "cantidad": 2, "formula": "alto - 26", "corte": "90°" },
            { "nombre": "Zoclo / Cabezal", "cantidad": 2, "formula": "(ancho - 185) / 2", "corte": "90°" }
        ],
        "vidrio": [
            { "nombre": "Vidrio fijo 4mm", "cantidad": 1, "ancho": "(ancho - 151) / 2", "alto": "alto - 125", "tipo": "4mm" },
            { "nombre": "Vidrio corredizo 4mm", "cantidad": 1, "ancho": "(ancho - 151) / 2", "alto": "alto - 135", "tipo": "4mm" }
        ],
        "notas": "🔧 Usar felpa en zoclo y cabezal para deslizamiento suave. Revisar escuadra antes de ensamblar.",
        "porcentajeHerrajesOverride": None,
        "esTemplado": False
    },
    "ventana_3_hojas_telescopica": {
        "nombre": "Ventana 3 hojas telescópica",
        "categoria": "ventanas",
        "icono": "🪟",
        "tipoVidrio": "6mm",
        "perfiles": [
            { "nombre": "Riel de 3\"", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Jamba de 3\" (cabezal)", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Adaptador paloma", "cantidad": 1, "formula": "ancho - 65", "corte": "90°" },
            { "nombre": "Jambas de 3\"", "cantidad": 2, "formula": "alto - 26", "corte": "90°" },
            { "nombre": "Zoclo / Cabezal de 3\"", "cantidad": 3, "formula": "(ancho - 167) / 3", "corte": "90°" },
            { "nombre": "Cerco chapa fijo", "cantidad": 1, "formula": "alto", "corte": "90°" },
            { "nombre": "Cerco chapa corredizo", "cantidad": 1, "formula": "alto - 40", "corte": "90°" },
            { "nombre": "Traslape fijo", "cantidad": 1, "formula": "alto", "corte": "90°" },
            { "nombre": "Traslape corredizo", "cantidad": 3, "formula": "alto - 40", "corte": "90°" }
        ],
        "vidrio": [
            { "nombre": "Vidrio fijo 6mm", "cantidad": 1, "ancho": "(ancho - 117) / 3", "alto": "alto - 95", "tipo": "6mm" },
            { "nombre": "Vidrio corredizo 6mm", "cantidad": 2, "ancho": "(ancho - 117) / 3", "alto": "alto - 135", "tipo": "6mm" }
        ],
        "notas": "⚠️ Requiere riel de 3 servicios. El adaptador paloma debe quedar centrado. Usar rodajas de nylon.",
        "porcentajeHerrajesOverride": 20.0,
        "esTemplado": False
    },
    "ventanal_oxxo": {
        "nombre": "Ventanal OXXO",
        "categoria": "ventanales",
        "icono": "🏪",
        "tipoVidrio": "6mm",
        "perfiles": [
            { "nombre": "Riel / Jamba c/mosquitero", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Jambas de 3\"", "cantidad": 2, "formula": "alto - 26", "corte": "90°" },
            { "nombre": "Zoclo / Cabezal de 3\"", "cantidad": 8, "formula": "(ancho - 330) / 4", "corte": "90°" },
            { "nombre": "Cerco chapa / Traslape fijo", "cantidad": 4, "formula": "alto - 30", "corte": "90°" },
            { "nombre": "Cerco chapa / Traslape corredizo", "cantidad": 4, "formula": "alto - 40", "corte": "90°" }
        ],
        "vidrio": [
            { "nombre": "Vidrio fijo 6mm", "cantidad": 2, "ancho": "(ancho - 265) / 4", "alto": "alto - 125", "tipo": "6mm" },
            { "nombre": "Vidrio corredizo 6mm", "cantidad": 2, "ancho": "(ancho - 265) / 4", "alto": "alto - 135", "tipo": "6mm" }
        ],
        "notas": "🏗️ Para vanos grandes, reforzar el riel inferior. Considerar dilatación térmica en climas extremos.",
        "porcentajeHerrajesOverride": 22.0,
        "esTemplado": False
    },
    "puerta_batiente_estandar": {
        "nombre": "Puerta batiente estándar",
        "categoria": "puertas",
        "icono": "🚪",
        "tipoVidrio": "6mm",
        "perfiles": [
            { "nombre": "Bolsa lisa cabezal", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Batiente cabezal", "cantidad": 1, "formula": "ancho - 64", "corte": "90°" },
            { "nombre": "Bolsas / Batientes verticales", "cantidad": 2, "formula": "alto - 32", "corte": "90°" },
            { "nombre": "Cercos chapa", "cantidad": 2, "formula": "alto - 47", "corte": "90°" },
            { "nombre": "Zoclo / Intermedio / Cabezal", "cantidad": 3, "formula": "ancho - 181", "corte": "90°" }
        ],
        "vidrio": [
            { "nombre": "Vidrio 6mm", "cantidad": 2, "ancho": "ancho - 191", "alto": "(alto - 205) / 2", "tipo": "6mm" }
        ],
        "notas": "🔑 La chapa se coloca a 950mm del piso. Usar 3 bisagras para puertas de más de 2m de alto.",
        "porcentajeHerrajesOverride": 25.0,
        "esTemplado": False
    },
    "puerta_ligera": {
        "nombre": "Puerta ligera",
        "categoria": "puertas",
        "icono": "🚪",
        "tipoVidrio": None,
        "perfiles": [
            { "nombre": "Batiente cabezal", "cantidad": 1, "formula": "ancho - 25", "corte": "90°" },
            { "nombre": "Batientes", "cantidad": 2, "formula": "alto", "corte": "90°" },
            { "nombre": "Cercos chapa", "cantidad": 2, "formula": "alto - 27", "corte": "90°" },
            { "nombre": "Zoclo / Intermedio", "cantidad": 2, "formula": "ancho - 139", "corte": "90°" }
        ],
        "vidrio": [],
        "notas": "📌 Puerta ciega sin vidrio. Ideal para closets o áreas de servicio. Usar panel de aluminio compuesto.",
        "porcentajeHerrajesOverride": 15.0,
        "esTemplado": False
    },
    "puerta_bano": {
        "nombre": "Puerta de baño",
        "categoria": "puertas",
        "icono": "🚿",
        "tipoVidrio": "4mm",
        "perfiles": [
            { "nombre": "Silla cabezal", "cantidad": 1, "formula": "ancho - 30", "corte": "90°" },
            { "nombre": "Silla", "cantidad": 2, "formula": "alto", "corte": "90°" },
            { "nombre": "Marco semilujo ancho", "cantidad": 2, "formula": "ancho - 42", "corte": "90°" },
            { "nombre": "Marco semilujo alto", "cantidad": 2, "formula": "alto - 30", "corte": "90°" }
        ],
        "vidrio": [
            { "nombre": "Plástico/Vidrio 4mm", "cantidad": 1, "ancho": "ancho - 112", "alto": "alto - 100", "tipo": "4mm" }
        ],
        "notas": "🚿 Asegurar ventilación inferior. Se puede usar plástico corrugado o vidrio esmerilado.",
        "porcentajeHerrajesOverride": 18.0,
        "esTemplado": False
    },
    "cancel_plastico_bano": {
        "nombre": "Cancel de baño plástico",
        "categoria": "canceles",
        "icono": "🚿",
        "tipoVidrio": None,
        "perfiles": [
            { "nombre": "Riel / Guía", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Jambas", "cantidad": 2, "formula": "alto - 30", "corte": "90°" },
            { "nombre": "Horizontales", "cantidad": 4, "formula": "(ancho + 30) / 2", "corte": "90°" },
            { "nombre": "Marcos económicos", "cantidad": 4, "formula": "alto - 50", "corte": "90°" }
        ],
        "vidrio": [
            { "nombre": "Hojas plástico", "cantidad": 2, "ancho": "(ancho - 30) / 2", "alto": "alto - 80", "tipo": None }
        ],
        "notas": "🛁 El plástico se corta con navaja. Dejar 3mm de holgura por lado para dilatación.",
        "porcentajeHerrajesOverride": 12.0,
        "esTemplado": False
    },
    "cancel_templado_estandar": {
        "nombre": "Cancel templado estándar",
        "categoria": "canceles",
        "icono": "🪞",
        "tipoVidrio": "templado8mm",
        "perfiles": [
            { "nombre": "Riel inferior de piso", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Jamba guía superior", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Jambas verticales", "cantidad": 2, "formula": "alto - 20", "corte": "90°" },
            { "nombre": "Perfil tapajunta vertical", "cantidad": 1, "formula": "alto - 30", "corte": "90°" }
        ],
        "vidrio": [
            {
                "nombre": "Hoja fija templada 8mm",
                "cantidad": 1,
                "ancho": "(ancho - 40) / 2",
                "alto": "alto - 25",
                "tipo": "templado8mm",
                "perforaciones": [
                    { "descripcion": "Perforación para corona superior", "distanciaBordeSuperior": 60, "distanciaBordeLateral": 40, "diametro": 12, "desdeAbajo": False },
                    { "descripcion": "Perforación para corona inferior", "distanciaBordeSuperior": 60, "distanciaBordeLateral": 40, "diametro": 12, "desdeAbajo": True }
                ]
            },
            {
                "nombre": "Hoja corrediza templada 8mm",
                "cantidad": 1,
                "ancho": "(ancho - 40) / 2",
                "alto": "alto - 35",
                "tipo": "templado8mm",
                "perforaciones": [
                    { "descripcion": "Perforación para corona superior", "distanciaBordeSuperior": 60, "distanciaBordeLateral": 40, "diametro": 12, "desdeAbajo": False },
                    { "descripcion": "Perforación para corona inferior", "distanciaBordeSuperior": 60, "distanciaBordeLateral": 40, "diametro": 12, "desdeAbajo": True },
                    { "descripcion": "Perforación para jaladera", "diametro": 25, "centroHorizontal": True, "alturaJaladera": 1000 }
                ]
            }
        ],
        "notas": "⚠️ VIDRIO TEMPLADO: Las perforaciones deben realizarse ANTES del templado. Diámetro estándar de corona: 12mm. La jaladera se centra horizontalmente a ~1000mm de altura.",
        "porcentajeHerrajesOverride": 28.0,
        "esTemplado": True
    },
    "ventana_abatible_estandar": {
        "nombre": "Ventana abatible estándar",
        "categoria": "ventanas",
        "icono": "🪟",
        "tipoVidrio": "6mm",
        "perfiles": [
            { "nombre": "Marco ventana (ancho)", "cantidad": 2, "formula": "ancho", "corte": "45°" },
            { "nombre": "Marco ventana (alto)", "cantidad": 2, "formula": "alto", "corte": "45°" },
            { "nombre": "Hoja ventana (ancho)", "cantidad": 2, "formula": "ancho - 42", "corte": "45°" },
            { "nombre": "Hoja ventana (alto)", "cantidad": 2, "formula": "alto - 42", "corte": "45°" },
            { "nombre": "Junquillo redondo (ancho)", "cantidad": 2, "formula": "ancho - 114", "corte": "45°" },
            { "nombre": "Junquillo redondo (alto)", "cantidad": 2, "formula": "alto - 114", "corte": "45°" }
        ],
        "vidrio": [
            { "nombre": "Vidrio 6mm", "cantidad": 1, "ancho": "ancho - 127", "alto": "alto - 127", "tipo": "6mm" }
        ],
        "notas": "📐 Cortes a 45° con ingletadora. Ensamblar junquillo en la hoja antes de cortar. Usar escuadras de alineación.",
        "porcentajeHerrajesOverride": 20.0,
        "esTemplado": False
    },
    "ventana_fija_1_1_2": {
        "nombre": "Ventana fija 1 1/2",
        "categoria": "ventanas",
        "icono": "🪟",
        "tipoVidrio": "4mm",
        "perfiles": [
            { "nombre": "Bolsa / Escalonado cabezal", "cantidad": 1, "formula": "ancho", "corte": "90°" },
            { "nombre": "Bolsas verticales", "cantidad": 2, "formula": "alto - 40", "corte": "90°" }
        ],
        "vidrio": [
            { "nombre": "Vidrio 4mm", "cantidad": 1, "ancho": "ancho - 48", "alto": "alto - 42", "tipo": "4mm" }
        ],
        "notas": "🪟 Ventana fija sin apertura. Sellar perimetralmente con silicón neutro.",
        "porcentajeHerrajesOverride": 10.0,
        "esTemplado": False
    }
}

def evaluar_formula_segura(formula: str, ancho: float, alto: float) -> float:
    """
    Evalúa expresiones algebraicas simples de despiece con variables 'ancho' y 'alto'.
    Garantiza ejecución segura sin eval arbitrario.
    """
    # Reemplazar identificadores de dimensiones
    expr = formula.replace("ancho", f"({float(ancho)})").replace("alto", f"({float(alto)})")

    # Sanitizar: permitir solo números, paréntesis, operadores y espacios
    if not re.match(r"^[\d\.\s\+\-\*\/\(\)]+$", expr):
        raise ValueError(f"Expresión matemática no permitida: {formula}")

    try:
        resultado = eval(expr, {"__builtins__": None}, {})
        return round(float(resultado), 2)
    except Exception as e:
        return 0.0

def calcular_despiece(
    product_key: str,
    ancho: float,
    alto: float,
    precios: Optional[Dict[str, float]] = None
) -> CalculateResponse:
    """
    Calcula despiece de perfiles, vidrios y costos estimados.
    """
    if product_key not in CATALOGO_PRODUCTOS:
        raise ValueError(f"Producto '{product_key}' no encontrado en el catálogo.")

    prod = CATALOGO_PRODUCTOS[product_key]
    precios = precios or {}
    precio_al = precios.get("precio_aluminio_metro", 180.0)
    precio_v4 = precios.get("precio_vidrio_4mm", 450.0)
    precio_v6 = precios.get("precio_vidrio_6mm", 620.0)
    precio_vt8 = precios.get("precio_vidrio_templado_8mm", 980.0)
    precio_vt10 = precios.get("precio_vidrio_templado_10mm", 1250.0)
    porc_herrajes_default = precios.get("porcentaje_herrajes", 18.0)
    costo_inst = precios.get("costo_instalacion", 0.0)

    # Cálculo de perfiles
    perfiles_res: List[PerfilComponent] = []
    total_mm_aluminio = 0.0
    for p in prod["perfiles"]:
        medida = evaluar_formula_segura(p["formula"], ancho, alto)
        perfiles_res.append(PerfilComponent(
            nombre=p["nombre"],
            cantidad=p["cantidad"],
            formula=p["formula"],
            corte=p["corte"],
            medida=medida
        ))
        total_mm_aluminio += medida * p["cantidad"]

    metros_aluminio = round(total_mm_aluminio / 1000.0, 2)
    costo_aluminio = round(metros_aluminio * precio_al, 2)

    # Cálculo de vidrios
    vidrios_res: List[VidrioComponent] = []
    total_area_vidrio_m2 = 0.0
    costo_vidrio = 0.0

    map_precios_vidrio = {
        "4mm": precio_v4,
        "6mm": precio_v6,
        "templado8mm": precio_vt8,
        "templado10mm": precio_vt10
    }

    for v in prod.get("vidrio", []):
        medida_ancho = evaluar_formula_segura(v["ancho"], ancho, alto) if "ancho" in v else None
        medida_alto = evaluar_formula_segura(v["alto"], ancho, alto) if "alto" in v else None

        perforaciones_list = None
        if "perforaciones" in v:
            perforaciones_list = [PerforacionVidrio(**perf) for perf in v["perforaciones"]]

        vidrios_res.append(VidrioComponent(
            nombre=v["nombre"],
            cantidad=v["cantidad"],
            tipo=v.get("tipo"),
            medidaAncho=medida_ancho,
            medidaAlto=medida_alto,
            perforaciones=perforaciones_list
        ))

        if v.get("tipo") and medida_ancho and medida_alto:
            area_m2 = (medida_ancho * medida_alto * v["cantidad"]) / 1_000_000.0
            total_area_vidrio_m2 += area_m2
            p_unit = map_precios_vidrio.get(v["tipo"], 0.0)
            costo_vidrio += area_m2 * p_unit

    costo_vidrio = round(costo_vidrio, 2)
    subtotal = round(costo_aluminio + costo_vidrio, 2)

    porc_herrajes = prod["porcentajeHerrajesOverride"] if prod.get("porcentajeHerrajesOverride") is not None else porc_herrajes_default
    costo_herrajes = round(subtotal * (porc_herrajes / 100.0), 2)
    total = round(subtotal + costo_herrajes + costo_inst, 2)

    area_total_m2 = round((ancho * alto) / 1_000_000.0, 2)

    return CalculateResponse(
        product_key=product_key,
        product_name=prod["nombre"],
        categoria=prod["categoria"],
        width_mm=ancho,
        height_mm=alto,
        area_m2=area_total_m2,
        perfiles=perfiles_res,
        vidrios=vidrios_res,
        costos=CostosDesglose(
            costoAluminio=costo_aluminio,
            costoVidrio=costo_vidrio,
            subtotal=subtotal,
            porcentajeHerrajes=porc_herrajes,
            costoHerrajes=costo_herrajes,
            costoInstalacion=costo_inst,
            total=total,
            metrosAluminio=metros_aluminio,
            areaVidrio=round(total_area_vidrio_m2, 3)
        ),
        notas=prod.get("notas"),
        esTemplado=prod.get("esTemplado", False)
    )
