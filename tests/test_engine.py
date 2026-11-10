import pytest
from backend.engine.calculator import calcular_despiece, evaluar_formula_segura, CATALOGO_PRODUCTOS
from backend.engine.optimizer import optimize_linear_cuts
from backend.schemas import CutPiece

def test_evaluar_formula_segura():
    assert evaluar_formula_segura("ancho", 1500, 2000) == 1500.0
    assert evaluar_formula_segura("alto - 26", 1500, 2000) == 1974.0
    assert evaluar_formula_segura("(ancho - 185) / 2", 1500, 2000) == 657.5

def test_evaluar_formula_invalida():
    with pytest.raises(ValueError):
        evaluar_formula_segura("import os; os.system('ls')", 1000, 1000)

def test_calcular_despiece_ventana_corrediza():
    res = calcular_despiece("ventana_corrediza_estandar", 1500, 2000)
    assert res.product_name == "Ventana corrediza estándar"
    assert len(res.perfiles) == 3
    assert len(res.vidrios) == 2
    assert res.costos.total > 0
    assert res.costos.subtotal == round(res.costos.costoAluminio + res.costos.costoVidrio, 2)

def test_calcular_despiece_cancel_templado():
    res = calcular_despiece("cancel_templado_estandar", 1600, 1900)
    assert res.esTemplado is True
    # Revisar perforaciones en vidrios
    hoja_fija = res.vidrios[0]
    assert hoja_fija.perforaciones is not None
    assert len(hoja_fija.perforaciones) == 2
    assert hoja_fija.perforaciones[0].diametro == 12.0

def test_linear_optimizer_single_bar():
    pieces = [
        CutPiece(label="Jamba 1", length_mm=2000, quantity=2),
        CutPiece(label="Riel", length_mm=1500, quantity=1)
    ]
    # Total mm = 2000*2 + 1500 = 5500 mm <= 6100 mm (1 barra con kerf)
    res = optimize_linear_cuts(pieces, bar_length_mm=6100.0, blade_thickness_mm=3.5)
    assert res.total_bars_required == 1
    assert len(res.bars) == 1
    assert res.total_waste_mm > 0
    assert res.total_waste_percent < 15.0

def test_linear_optimizer_multiple_bars():
    pieces = [
        CutPiece(label="Perfil largo", length_mm=3200, quantity=3)
    ]
    # Cada pieza mide 3200mm, por lo que no caben 2 en una sola barra de 6100mm. Requiere 3 barras.
    res = optimize_linear_cuts(pieces, bar_length_mm=6100.0, blade_thickness_mm=3.5)
    assert res.total_bars_required == 3
    assert len(res.bars) == 3

def test_linear_optimizer_exceeds_bar():
    pieces = [
        CutPiece(label="Perfil imposible", length_mm=6500, quantity=1)
    ]
    with pytest.raises(ValueError):
        optimize_linear_cuts(pieces, bar_length_mm=6100.0)
