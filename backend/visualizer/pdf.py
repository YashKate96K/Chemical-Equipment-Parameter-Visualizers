from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, black, white, HexColor
from .utils import parse_rows, compute_quality, compute_correlations, compute_variance_skewness


def build_pdf(dataset):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Colors
    COLOR_PRIMARY = HexColor("#00897B")
    SECTION_BG = Color(0.95, 0.95, 0.95)

    # Column positions
    LEFT_COL_X = 40
    RIGHT_COL_X = width / 2 + 20
    TOP = height - 100
    BOTTOM = 60

    # Track position
    column = 1
    y = TOP

    # ------------ COLUMN MANAGER ------------
    def new_page():
        nonlocal y, column
        c.showPage()
        draw_header()
        column = 1
        y = TOP

    def next_column():
        nonlocal column, y
        if column == 1:
            column = 2
            y = TOP
        else:
            new_page()

    def get_x(indent):
        if column == 1:
            return LEFT_COL_X + indent
        else:
            return RIGHT_COL_X + indent

    def ensure_space(h):
        nonlocal y
        if y - h < BOTTOM:
            next_column()

    # ------------ HEADER ------------
    def draw_header():
        c.setFillColor(COLOR_PRIMARY)
        c.rect(0, height - 75, width, 75, fill=1, stroke=0)

        title = "Chemical Equipment Parameter Report"
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(white)
        tw = c.stringWidth(title, "Helvetica-Bold", 20)
        c.drawString((width - tw) / 2, height - 45, title)

        c.setFont("Helvetica", 10)
        c.drawString(40, height - 65, f"File: {dataset.filename}")

        created = f"Created: {dataset.created_at:%Y-%m-%d %H:%M:%S}"
        cw = c.stringWidth(created, "Helvetica", 10)
        c.drawString(width - 40 - cw, height - 65, created)

    draw_header()

    # ------------ TEXT BLOCKS ------------
    def section(title):
        nonlocal y
        ensure_space(40)
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(COLOR_PRIMARY)
        c.drawString(get_x(0), y, title)
        y -= 18

        # tiny divider
        c.setFillColor(SECTION_BG)
        c.rect(get_x(0), y, 200, 3, fill=1, stroke=0)
        y -= 15

    def line(txt, indent=0, bullet=False):
        nonlocal y
        ensure_space(15)
        c.setFont("Helvetica", 10)
        c.setFillColor(black)

        x = get_x(indent)
        if bullet:
            c.drawString(x - 8, y, "•")

        c.drawString(x, y, txt)
        y -= 14

    # ------------ DATA ------------
    summary = dataset.summary_json or {}

    # -------- Dataset Overview --------
    section("Dataset Overview")

    if summary.get("row_count"):
        line(f"Total rows: {summary['row_count']}")

    if summary.get("all_columns"):
        line("Columns:")
        for col in summary["all_columns"]:
            if col in ("Record", "record"):
                continue
            line(col, indent=20, bullet=True)

    # -------- Summary Stats --------
    section("Summary Statistics")

    if summary.get("averages"):
        line("Averages:")
        for k, v in summary["averages"].items():
            if k in ("Record", "record"):
                continue
            try:
                v = f"{float(v):.3f}"
            except:
                pass
            line(f"{k}: {v}", indent=20, bullet=True)

    if summary.get("min"):
        line("Minimum Values:")
        for k, v in summary["min"].items():
            if k in ("Record", "record"):
                continue
            line(f"{k}: {v}", indent=20, bullet=True)

    if summary.get("max"):
        line("Maximum Values:")
        for k, v in summary["max"].items():
            if k in ("Record", "record"):
                continue
            line(f"{k}: {v}", indent=20, bullet=True)

    if summary.get("type_distribution"):
        line("Type Distribution:")
        for k, v in summary["type_distribution"].items():
            line(f"{k}: {v}", indent=20, bullet=True)

    # -------- Advanced analytics --------
    try:
        file_obj = dataset.file
        file_obj.open("rb")
        fb = file_obj.read()
        file_obj.close()

        header, rows = parse_rows(fb, dataset.file.name)
        numeric_cols = summary.get("numeric_columns") or [
            c for c in header if c not in ("Type", "Equipment Name")
        ]
        # Treat Record as an ID column, not a numeric feature
        numeric_cols = [c for c in numeric_cols if c not in ("Record", "record")]

        quality = compute_quality(header, rows)
        correlations = compute_correlations(rows, numeric_cols)
        var_skew = compute_variance_skewness(rows, numeric_cols)

        section("Data Quality")

        missing = quality.get("missing_values", {})
        if missing:
            line("Missing Values (Top 5):")
            # Skip Record column in missing-value listing
            filtered_missing = {k: v for k, v in missing.items() if k not in ("Record", "record")}
            for col, cnt in sorted(filtered_missing.items(), key=lambda a: a[1], reverse=True)[:5]:
                line(f"{col}: {cnt}", indent=20, bullet=True)

        if quality.get("duplicate_rows", {}).get("count"):
            line(f"Duplicate Rows: {quality['duplicate_rows']['count']}",
                 indent=20, bullet=True)

        section("Strongest Correlations")
        for pair in correlations.get("strongest_pairs", []):
            a, b = pair.get("cols", ("", ""))
            r = pair.get("corr")
            try:
                r = f"{float(r):.2f}"
            except:
                pass
            line(f"{a} vs {b}: r = {r}", indent=20, bullet=True)

        section("Variance & Skewness (Top 5)")
        # Exclude Record column from variance/skewness listing
        filtered_vs = {k: v for k, v in var_skew.items() if k not in ("Record", "record")}
        ordered = sorted(filtered_vs.items(), key=lambda a: a[1].get("variance", 0), reverse=True)
        for col, st in ordered[:5]:
            v = st.get("variance")
            sk = st.get("skewness")

            try:
                v = f"{float(v):.3f}"
            except:
                pass
            try:
                sk = f"{float(sk):.3f}"
            except:
                pass

            line(f"{col}: variance={v}, skewness={sk}", indent=20, bullet=True)

    except:
        section("Additional Analytics")
        line("(Analytics could not be computed.)")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()



