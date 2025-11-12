from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_pdf(dataset):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "Chemical Equipment Parameter Report")

    c.setFont("Helvetica", 10)
    y = height - 90
    c.drawString(40, y, f"Filename: {dataset.filename}")
    y -= 14
    c.drawString(40, y, f"Created: {dataset.created_at:%Y-%m-%d %H:%M:%S}")
    y -= 24

    s = dataset.summary_json
    def line(txt):
        nonlocal y
        c.drawString(40, y, txt)
        y -= 14

    line("Averages:")
    for k, v in s.get('averages', {}).items():
        line(f"  - {k}: {v:.3f}")
    line("Min:")
    for k, v in s.get('min', {}).items():
        line(f"  - {k}: {v}")
    line("Max:")
    for k, v in s.get('max', {}).items():
        line(f"  - {k}: {v}")

    line("Type distribution:")
    for k, v in s.get('type_distribution', {}).items():
        line(f"  - {k}: {v}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
