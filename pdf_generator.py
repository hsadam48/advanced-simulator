from __future__ import annotations

import io
import os
import tempfile

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def dataframe_to_pdf_table(df: pd.DataFrame, max_rows: int = 45):
    styles = getSampleStyleSheet()
    cell = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=6.5, leading=8)
    head = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontSize=6.5,
        leading=8,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    clean = df.head(max_rows).copy().fillna("")
    data = [[Paragraph(str(c), head) for c in clean.columns]]
    data += [[Paragraph(str(v), cell) for v in row] for row in clean.astype(str).values.tolist()]

    tbl = Table(data, colWidths=[780 / max(1, len(clean.columns))] * len(clean.columns))
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 2),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return tbl


def save_uploaded_image(image_bytes, image_name):
    if not image_bytes or not image_name:
        return None

    suffix = os.path.splitext(image_name)[1] or ".png"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(image_bytes)
    tmp.flush()
    tmp.close()
    return tmp.name


def create_pdf(
    project_name,
    project_address,
    prepared_by,
    logo_bytes,
    logo_name,
    photo_bytes,
    photo_name,
    input_df,
    analysis_df,
    rec_df,
    bm_df,
    simulation_summary_df=None,
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=25,
        leftMargin=25,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )
    sub = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )
    sec = ParagraphStyle(
        "Sec",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=5,
    )

    elements = []

    logo = save_uploaded_image(logo_bytes, logo_name)
    photo = save_uploaded_image(photo_bytes, photo_name)

    if logo:
        elements += [Image(logo, width=110, height=55), Spacer(1, 10)]

    elements += [
        Paragraph("Vertical Transportation Engineering Review", title),
        Spacer(1, 8),
        Paragraph(f"<b>Project:</b> {project_name}", sub),
        Paragraph(f"<b>Address:</b> {project_address or '-'}", sub),
        Paragraph(f"<b>Prepared By:</b> {prepared_by}", sub),
        Spacer(1, 14),
    ]

    if photo:
        elements += [Image(photo, width=360, height=190), Spacer(1, 14)]

    elements += [
        Paragraph(
            "Benchmark basis: CIBSE Guide D / ISO 8100-32 style target metrics used for preliminary comparison.",
            sub,
        ),
        Paragraph(
            "Note: final traffic analysis must be verified by elevator specialist/manufacturer.",
            sub,
        ),
        Spacer(1, 18),
        Paragraph("Tower & Lift Inputs", sec),
        dataframe_to_pdf_table(input_df),
        Paragraph("Benchmark Targets", sec),
        dataframe_to_pdf_table(bm_df),
        Paragraph("Result Recommendations", sec),
        dataframe_to_pdf_table(rec_df),
        Paragraph("Detailed Benchmark Analysis", sec),
        dataframe_to_pdf_table(analysis_df),
    ]

    if simulation_summary_df is not None and not simulation_summary_df.empty:
        elements += [
            Paragraph("Advanced Simulation Summary", sec),
            dataframe_to_pdf_table(simulation_summary_df),
        ]

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()