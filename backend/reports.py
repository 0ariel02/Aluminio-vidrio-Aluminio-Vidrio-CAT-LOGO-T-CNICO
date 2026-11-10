import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_quote_pdf(quote_data: dict, tenant_data: dict) -> bytes:
    """
    Genera un documento PDF profesional con logotipo, datos fiscales del taller,
    desglose técnico de cortes y cotización comercial.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0077B6')
    )

    subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B')
    )

    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )

    story = []

    # Encabezado con datos del taller / Tenant
    tenant_name = tenant_data.get("name", "Carpintería Aluminio & Vidrio Plascencia")
    rfc = tenant_data.get("rfc", "RFC: XAXX010101000")
    address = tenant_data.get("address", "Guadalajara, Jalisco, México")
    phone = tenant_data.get("phone", "+52 33 2082 7128")
    email = tenant_data.get("email", "contacto@aluminioyvidrio.mx")

    folio = quote_data.get("folio", f"COT-{datetime.utcnow().strftime('%Y%m%d%H%M')}")
    fecha = datetime.utcnow().strftime('%d/%m/%Y %H:%M')

    header_table_data = [
        [
            Paragraph(f"<b>{tenant_name}</b><br/>{rfc} | {address}<br/>Tel: {phone} | {email}", subtitle_style),
            Paragraph(f"<b>COTIZACIÓN TÉCNICA</b><br/><b>Folio:</b> {folio}<br/><b>Fecha:</b> {fecha}", ParagraphStyle(
                'FolioStyle', parent=subtitle_style, alignment=2
            ))
        ]
    ]
    header_table = Table(header_table_data, colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#0077B6'))
    ]))
    story.append(header_table)
    story.append(Spacer(1, 14))

    # Resumen del producto
    prod_name = quote_data.get("product_name", "Ventana Corrediza")
    width = quote_data.get("width_mm", 1500)
    height = quote_data.get("height_mm", 2000)
    area = quote_data.get("area_m2", round((width * height) / 1e6, 2))

    summary_data = [
        [
            Paragraph("<b>Producto:</b>", subtitle_style), Paragraph(str(prod_name), subtitle_style),
            Paragraph("<b>Dimensiones:</b>", subtitle_style), Paragraph(f"{width} × {height} mm ({area} m²)", subtitle_style)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[70, 200, 90, 180])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # Despiece de perfiles (Hoja de taller)
    story.append(Paragraph("Despiece Técnico de Perfiles (Hoja de Taller)", section_title))
    perfiles = quote_data.get("perfiles", [])
    perfil_rows = [["Cant.", "Perfil", "Corte", "Longitud (mm)"]]
    for p in perfiles:
        perfil_rows.append([
            f"{p.get('cantidad', 1)}x",
            p.get('nombre', ''),
            p.get('corte', '90°'),
            f"{p.get('medida', 0)} mm"
        ])

    perfil_table = Table(perfil_rows, colWidths=[50, 280, 80, 130])
    perfil_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#005A8C')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (-1,-1), 'CENTER')
    ]))
    story.append(perfil_table)
    story.append(Spacer(1, 14))

    # Despiece de vidrios
    vidrios = quote_data.get("vidrios", [])
    if vidrios:
        story.append(Paragraph("Cédula de Vidrios y Cristales", section_title))
        vidrio_rows = [["Cant.", "Descripción / Vidrio", "Tipo", "Dimensiones (mm)"]]
        for v in vidrios:
            w_v = v.get("medidaAncho", "")
            h_v = v.get("medidaAlto", "")
            dim = f"{w_v} × {h_v} mm" if w_v else f"{h_v} mm"
            vidrio_rows.append([
                f"{v.get('cantidad', 1)}x",
                v.get("nombre", ""),
                v.get("tipo", "Vidrio"),
                dim
            ])
        vidrio_table = Table(vidrio_rows, colWidths=[50, 250, 110, 130])
        vidrio_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (2,0), (-1,-1), 'CENTER')
        ]))
        story.append(vidrio_table)
        story.append(Spacer(1, 14))

    # Resumen Financiero
    costos = quote_data.get("costos", {})
    if costos:
        story.append(Paragraph("Resumen de Cotización Comercial", section_title))
        cost_rows = [
            ["Concepto", "Monto (MXN)"],
            [f"Aluminio ({costos.get('metrosAluminio', 0)} m lineales)", f"${costos.get('costoAluminio', 0.0):.2f}"],
            [f"Vidrio ({costos.get('areaVidrio', 0)} m²)", f"${costos.get('costoVidrio', 0.0):.2f}"],
            ["Subtotal materiales", f"${costos.get('subtotal', 0.0):.2f}"],
            [f"Herrajes e insumos ({costos.get('porcentajeHerrajes', 18)}%)", f"${costos.get('costoHerrajes', 0.0):.2f}"],
        ]
        if costos.get('costoInstalacion', 0) > 0:
            cost_rows.append(["Costo de Instalación", f"${costos.get('costoInstalacion', 0.0):.2f}"])
        cost_rows.append(["TOTAL ESTIMADO", f"${costos.get('total', 0.0):.2f} MXN"])

        cost_table = Table(cost_rows, colWidths=[380, 160])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0077B6')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#FEF3C7')),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.HexColor('#92400E'))
        ]))
        story.append(cost_table)

    # Notas al pie
    story.append(Spacer(1, 16))
    notas = quote_data.get("notas", "Precios sujetos a variaciones del mercado. Vigencia de cotización: 15 días.")
    footer_p = Paragraph(f"<b>Observaciones:</b> {notas}", subtitle_style)
    story.append(footer_p)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
