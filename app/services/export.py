from io import BytesIO
from fastapi.responses import StreamingResponse


def export_as_txt(chat_name, records, doc_names, session_id):
    from datetime import datetime

    lines = []
    lines.append("PDF Assistant — Chat Export")
    lines.append("=" * 50)
    lines.append(f"Chat: {chat_name}")
    lines.append(f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Documents: {', '.join(doc_names) if doc_names else 'None'}")
    lines.append(f"Messages: {len(records)}")
    lines.append("=" * 50)
    lines.append("")

    for i, record in enumerate(records, 1):
        lines.append(f"Q{i}: {record.question}")
        lines.append(f"A{i}: {record.answer}")
        if record.sources:
            lines.append(f"Sources: {record.sources}")
        if record.confidence:
            lines.append(f"Confidence: {record.confidence}")
        lines.append("")

    content = "\n".join(lines)
    buffer = BytesIO(content.encode("utf-8"))
    filename = f"{chat_name.replace(' ', '_')}_export.txt"

    return StreamingResponse(
        buffer,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def export_as_pdf(chat_name, records, doc_names, session_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    )
    from datetime import datetime

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=20, fontName='Helvetica-Bold',
        textColor=HexColor('#111111'), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica',
        textColor=HexColor('#666666'), spaceAfter=2
    )
    question_style = ParagraphStyle(
        'Question', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold',
        textColor=HexColor('#111111'),
        backColor=HexColor('#f5f5f5'),
        borderPad=8, leftIndent=10, rightIndent=10,
        spaceBefore=12, spaceAfter=6
    )
    answer_style = ParagraphStyle(
        'Answer', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica',
        textColor=HexColor('#333333'),
        leftIndent=10, rightIndent=10,
        spaceAfter=4, leading=16
    )
    meta_style = ParagraphStyle(
        'Meta', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica',
        textColor=HexColor('#999999'),
        leftIndent=10, spaceAfter=8
    )

    story = []

    story.append(Paragraph("PDF Assistant", title_style))
    story.append(Paragraph(f"Chat Export: {chat_name}", subtitle_style))
    story.append(Paragraph(
        f"Exported on {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}",
        subtitle_style
    ))
    if doc_names:
        story.append(Paragraph(
            f"Documents: {', '.join(doc_names)}", subtitle_style
        ))
    story.append(Paragraph(f"Total messages: {len(records)}", subtitle_style))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e0e0e0')))
    story.append(Spacer(1, 6*mm))

    for i, record in enumerate(records, 1):
        story.append(Paragraph(f"Q{i}: {record.question}", question_style))
        answer_text = record.answer.replace('\n', '<br/>')
        story.append(Paragraph(answer_text, answer_style))

        meta_parts = []
        if record.confidence:
            meta_parts.append(f"Confidence: {record.confidence}")
        if record.sources:
            meta_parts.append(f"Sources: {record.sources}")
        if record.created_at:
            meta_parts.append(record.created_at.strftime('%Y-%m-%d %H:%M'))
        if meta_parts:
            story.append(Paragraph(" · ".join(meta_parts), meta_style))

        story.append(HRFlowable(
            width="100%", thickness=0.5, color=HexColor('#eeeeee')
        ))

    doc.build(story)
    buffer.seek(0)

    filename = f"{chat_name.replace(' ', '_')}_export.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )