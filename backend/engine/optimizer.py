from typing import List, Dict, Any
from backend.schemas import CutPiece, BarPattern, OptimizationResponse

def optimize_linear_cuts(
    pieces: List[CutPiece],
    bar_length_mm: float = 6100.0,
    blade_thickness_mm: float = 3.5
) -> OptimizationResponse:
    """
    Optimizador de corte 1D (Linear Cutting / Nesting) para barras estándar de perfilería de 6.10 metros (6100 mm).
    Implementa heurística First-Fit Decreasing (FFD) con consideración de espesor de disco (kerf de sierra).
    Minimiza barras necesarias y porcentaje de desperdicio para talleres e instaladores.
    """
    # Expandir piezas según su cantidad
    expanded_items: List[Dict[str, Any]] = []
    total_cut_length = 0.0

    for p in pieces:
        if p.length_mm <= 0:
            continue
        if p.length_mm > bar_length_mm:
            raise ValueError(
                f"La pieza '{p.label}' de longitud {p.length_mm} mm excede la barra estándar de {bar_length_mm} mm."
            )
        for i in range(p.quantity):
            expanded_items.append({
                "label": p.label,
                "length_mm": round(p.length_mm, 2)
            })
            total_cut_length += p.length_mm

    # Ordenar de mayor a menor (First-Fit Decreasing)
    expanded_items.sort(key=lambda x: x["length_mm"], reverse=True)

    # Cada barra rastrea su espacio utilizado y lista de cortes
    bars: List[Dict[str, Any]] = []

    for item in expanded_items:
        placed = False
        piece_len = item["length_mm"]

        for bar in bars:
            # Si la barra ya tiene cortes, añadir el kerf del disco de corte
            additional_space = piece_len + (blade_thickness_mm if bar["cuts"] else 0.0)
            if bar["used_length_mm"] + additional_space <= bar_length_mm:
                bar["cuts"].append({
                    "label": item["label"],
                    "length_mm": piece_len
                })
                bar["used_length_mm"] += additional_space
                placed = True
                break

        if not placed:
            # Abrir una nueva barra de 6.10m
            bars.append({
                "bar_index": len(bars) + 1,
                "used_length_mm": piece_len,
                "cuts": [{
                    "label": item["label"],
                    "length_mm": piece_len
                }]
            })

    # Formatear el resultado
    bar_patterns: List[BarPattern] = []
    total_stock_used = len(bars) * bar_length_mm
    total_waste = 0.0

    for idx, b in enumerate(bars):
        # Desperdicio real = longitud de barra - suma de cortes de piezas (el kerf se considera pérdida)
        sum_pieces = sum(c["length_mm"] for c in b["cuts"])
        waste_mm = round(bar_length_mm - sum_pieces, 2)
        waste_percent = round((waste_mm / bar_length_mm) * 100.0, 2)
        total_waste += waste_mm

        bar_patterns.append(BarPattern(
            bar_index=idx + 1,
            used_length_mm=round(sum_pieces, 2),
            waste_length_mm=waste_mm,
            waste_percent=waste_percent,
            cuts=b["cuts"]
        ))

    total_waste_percent = round((total_waste / total_stock_used) * 100.0, 2) if total_stock_used > 0 else 0.0

    return OptimizationResponse(
        total_bars_required=len(bars),
        bar_standard_length_mm=bar_length_mm,
        blade_thickness_mm=blade_thickness_mm,
        total_cut_length_mm=round(total_cut_length, 2),
        total_stock_used_mm=round(total_stock_used, 2),
        total_waste_mm=round(total_waste, 2),
        total_waste_percent=total_waste_percent,
        bars=bar_patterns
    )
