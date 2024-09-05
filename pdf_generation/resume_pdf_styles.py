import os
from .. import config

from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph


def generate_doc_template(name, job_data_location):
    """
    Generate and return a SimpleDocTemplate for the resume PDF.

    Args:
        name (str): The name of the resume author.
        job_data_location (str): The path where the PDF will be saved.

    Returns:
        tuple: A tuple containing the document template for the resume PDF and the PDF location.
    """
    author_name_formatted = name.replace(" ", "_") + "_resume"
    pdf_location = os.path.join(job_data_location, f"{author_name_formatted}.pdf")
    doc = SimpleDocTemplate(
        pdf_location,
        pagesize=A4,
        showBoundary=0,
        leftMargin=0.1 * inch,
        rightMargin=0.1 * inch,
        topMargin=0.1 * inch,
        bottomMargin=0.1 * inch,
        title=f"{author_name_formatted}",
        author=name,
    )
    return (doc, pdf_location)


DEFAULT_PADDING = (1, 1)
DOCUMENT_ALIGNMENT = [
    ("ALIGN", (0, 0), (0, -1), "LEFT"),
    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
]
DEBUG_STYLE = ("GRID", (0, 0), (-1, -1), 0, colors.black)

PAGE_WIDTH, PAGE_HEIGHT = A4
FULL_COLUMN_WIDTH = PAGE_WIDTH - 1 * inch
JSON_PATH = os.path.join(config.DATA_PATH, "data.json")

FONT_PATHS = {
    "regular": os.path.join(config.RESOURCES_PATH, "fonts/calibri.ttf"),
    "bold": os.path.join(config.RESOURCES_PATH, "fonts/calibrib.ttf"),
    "italic": os.path.join(config.RESOURCES_PATH, "fonts/calibrii.ttf"),
}
FONT_NAMES = {
    "regular": "FONT_Regular",
    "bold": "FONT_Bold",
    "italic": "FONT_Italic",
}

sample_style_sheets = getSampleStyleSheet()

PARAGRAPH_STYLES = {
    "bullet_points": ParagraphStyle(
        name="bullet_points_paragraph",
        leftIndent=12,
        fontName=FONT_NAMES["regular"],
        fontSize=11,
        leading=12,
        alignment=0,
        justifyBreaks=0,
        justifyLastLine=0,
    ),
    "last_bullet_point": ParagraphStyle(
        name="last_bullet_point",
        leftIndent=12,
        fontName=FONT_NAMES["regular"],
        fontSize=11,
        leading=12,
        alignment=0,
        justifyBreaks=0,
        justifyLastLine=0,
    ),
    "name": ParagraphStyle(
        name="name_paragraph",
        fontName=FONT_NAMES["bold"],
        fontSize=14,
        textTransform="uppercase",
        alignment=TA_CENTER,
        leading=12,
    ),
    "link": ParagraphStyle(
        name='Hyperlink',
        fontName=FONT_NAMES["regular"],
        fontSize=11,
        parent=sample_style_sheets['BodyText'],
        textColor=colors.blue,
        underline=True,
    ),
    "link-no-hyperlink": ParagraphStyle(
        name='Hyperlink',
        fontName=FONT_NAMES["regular"],
        fontSize=11,
    ),
    "normal": ParagraphStyle(
        name="normal_paragraph",
        fontName=FONT_NAMES["regular"],
        fontSize=11,
        leading=12,
    ),
    "education": ParagraphStyle(
        name="education_paragraph",
        fontName=FONT_NAMES["regular"],
        fontSize=11,
        leading=12,
    ),
    "space": ParagraphStyle(
        name="space_paragraph",
        fontName=FONT_NAMES["regular"],
        fontSize=0,
        leading=0,
    ),
    "skills": ParagraphStyle(
        name="skills_paragraph",
        fontName=FONT_NAMES["regular"],
        fontSize=11,
        leading=12,
    ),
    "contact": ParagraphStyle(
        name="contact_paragraph",
        fontName=FONT_NAMES["regular"],
        fontSize=11,
        leading=12,
        alignment=TA_CENTER,
    ),
    "section": ParagraphStyle(
        name="section_paragraph",
        fontName=FONT_NAMES["bold"],
        fontSize=11,
        textTransform="uppercase",
    ),
    "objective": ParagraphStyle(
        name="objective_paragraph",
        fontName=FONT_NAMES["regular"],
        fontSize=11,
        leading=13,
        alignment=0,  # TA_LEFT
        justifyBreaks=0,
        justifyLastLine=0,
    ),
    "company_heading": ParagraphStyle(
        name="company_heading_paragraph",
        fontName=FONT_NAMES["bold"],
        fontSize=11,
        leading=10,
    ),
    "company_title": ParagraphStyle(
        name="company_title_paragraph",
        fontName=FONT_NAMES["italic"],
        fontSize=11,
        leading=10,
    ),
    "company_duration": ParagraphStyle(
        name="company_duration_paragraph",
        fontName=FONT_NAMES["italic"],
        fontSize=11,
        alignment=TA_RIGHT,
        leading=8,
    ),
    "company_location": ParagraphStyle(
        name="company_location_paragraph",
        fontName=FONT_NAMES["italic"],
        fontSize=11,
        alignment=TA_RIGHT,
        leading=8,
    ),
}
