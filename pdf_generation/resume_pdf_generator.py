import configparser
import json
import os
import random
from .. import config
import subprocess

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

class ResumePDFGenerator:
    """
    A class to generate a resume PDF from JSON data using the ReportLab library.
    """

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

    PARAGRAPH_STYLES = {
        "job_details": ParagraphStyle(
            name="job_details_paragraph",
            leftIndent=12,
            fontName=FONT_NAMES["regular"],
            fontSize=11,
            leading=12,
            alignment=0,  # TA_LEFT
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
            leading=8,
        ),
        "company_title": ParagraphStyle(
            name="company_title_paragraph",
            fontName=FONT_NAMES["italic"],
            fontSize=11,
            leading=8,
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

    def __init__(self):
        """
        Initialize the ResumePDFGenerator by registering fonts.
        """
        self._register_fonts()

    def _register_fonts(self):
        """
        Register fonts for use in the PDF.
        """
        for style, path in self.FONT_PATHS.items():
            pdfmetrics.registerFont(ttfonts.TTFont(self.FONT_NAMES[style], path))

    def _append_section_table_style(self, table_styles, row_index):
        """
        Append styles for section headers in the table.

        Args:
            table_styles (list): List of table styles to be extended.
            row_index (int): The current row index in the table.
        """
        table_styles.extend(
            [
                ("TOPPADDING", (0, row_index), (1, row_index), 5),
                ("BOTTOMPADDING", (0, row_index), (1, row_index), 2),
                ("LINEBELOW", (0, row_index), (-1, row_index), 0.1, colors.black),
            ]
        )

    def generate_resume(
        self,
        file_path,
        data,
        author=config.CONFIG_INI["author"],
        email=config.CONFIG_INI["email"],
        address=config.CONFIG_INI["address"],
        phone=config.CONFIG_INI["phone"],
        github=config.CONFIG_INI["github"],
        linkedin=config.CONFIG_INI["linkedin"],
        debug=config.CONFIG_INI["debug"],
    ):
        """
        Generate a resume PDF from JSON data.

        Args:
            file_path (str): The path where the PDF will be saved.
            data (dict): The JSON data containing resume information.
            author (str): The author's name.
            email (str): The author's email.
            address (str): The author's address.
            phone (str): The author's phone number.
            github (str): The author's GitHub profile.
            linkedin (str): The author's LinkedIn profile.
            debug (str): Debug flag to show grid lines in the PDF.
        """
        author_name_formatted = author.replace(" ", "_") + "_resume"
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            showBoundary=0,
            leftMargin=0.1 * inch,
            rightMargin=0.1 * inch,
            topMargin=0.1 * inch,
            bottomMargin=0.1 * inch,
            title=f"{author_name_formatted}",
            author=author,
        )

        table_data = []
        table_styles = []
        row_index = 0

        if debug == "true":
            table_styles.append(("GRID", (0, 0), (-1, -1), 0, colors.black))

        table_styles.extend(
            [
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )

        # Add name and contact information
        table_data.append([Paragraph(author, self.PARAGRAPH_STYLES["name"])])
        table_styles.extend(
            [
                ("BOTTOMPADDING", (0, row_index), (-1, row_index), 1),
                ("SPAN", (0, row_index), (1, row_index)),
            ]
        )
        row_index += 1

        table_data.append(
            [
                Paragraph(
                    f"{email} | {phone} | {linkedin} | {github} | {address}",
                    self.PARAGRAPH_STYLES["contact"],
                )
            ]
        )
        table_styles.extend(
            [
                ("BOTTOMPADDING", (0, row_index), (-1, row_index), 1),
                ("SPAN", (0, row_index), (1, row_index)),
            ]
        )
        row_index += 1

        # Add summary
        table_data.append([Paragraph("Objective", self.PARAGRAPH_STYLES["section"])])
        self._append_section_table_style(table_styles, row_index)
        table_styles.append(("SPAN", (0, row_index), (-1, row_index)))
        row_index += 1

        table_data.append(
            [Paragraph(data["objective"], self.PARAGRAPH_STYLES["objective"])]
        )
        table_styles.extend(
            [
                ("BOTTOMPADDING", (0, row_index), (-1, row_index), 1),
                ("SPAN", (0, row_index), (-1, row_index)),
            ]
        )
        row_index += 1

        # Add experience
        table_data.append([Paragraph("Experience", self.PARAGRAPH_STYLES["section"])])
        self._append_section_table_style(table_styles, row_index)
        row_index += 1

        for job in data["experience"]:
            skip_cof = (
                job["company"] == "Capital One"
                and job["title"] != "Product Manager, Pricing & Valuations"
            )

            if not skip_cof:
                table_data.append(
                    [
                        Paragraph(
                            job["company"], self.PARAGRAPH_STYLES["company_heading"]
                        ),
                        Paragraph(
                            job["duration"], self.PARAGRAPH_STYLES["company_duration"]
                        ),
                    ]
                )
                table_styles.append(("TOPPADDING", (0, row_index), (1, row_index), 0))
                row_index += 1

                table_data.append(
                    [
                        Paragraph(job["title"], self.PARAGRAPH_STYLES["company_title"]),
                        Paragraph(
                            job["location"], self.PARAGRAPH_STYLES["company_location"]
                        ),
                    ]
                )
                table_styles.append(("TOPPADDING", (0, row_index), (1, row_index), 0))
                table_styles.append(
                    ("BOTTOMPADDING", (0, row_index), (1, row_index), 5)
                )
                row_index += 1
            else:
                table_data.append(
                    [
                        Paragraph(job["title"], self.PARAGRAPH_STYLES["company_title"]),
                    ]
                )
                table_styles.append(("TOPPADDING", (0, row_index), (1, row_index), 0))
                table_styles.append(
                    ("BOTTOMPADDING", (0, row_index), (1, row_index), 5)
                )
                row_index += 1

            for line in job["description"]:
                table_data.append(
                    [
                        Paragraph(
                            line,
                            bulletText="•",
                            style=self.PARAGRAPH_STYLES["job_details"],
                        )
                    ]
                )
                table_styles.extend(
                    [
                        ("TOPPADDING", (0, row_index), (1, row_index), 1),
                        ("BOTTOMPADDING", (0, row_index), (1, row_index), 0),
                        ("SPAN", (0, row_index), (1, row_index)),
                    ]
                )
                row_index += 1

            if not skip_cof:
                table_data.append([Paragraph("", self.PARAGRAPH_STYLES["space"])])
                table_styles.extend(
                    [
                        ("TOPPADDING", (0, row_index), (1, row_index), 0),
                        ("BOTTOMPADDING", (0, row_index), (1, row_index), 0),
                        ("SPAN", (0, row_index), (1, row_index)),
                    ]
                )
                row_index += 1

        # Add education
        table_data.append([Paragraph("Education", self.PARAGRAPH_STYLES["section"])])
        self._append_section_table_style(table_styles, row_index)
        row_index += 1

        for edu in data["education"]:
            table_data.append(
                [
                    Paragraph(
                        f"<font name='{self.FONT_NAMES['bold']}'>{edu['university']}</font>, {edu['degree']}",
                        self.PARAGRAPH_STYLES["education"],
                    )
                ]
            )
            table_styles.append(("TOPPADDING", (0, row_index), (1, row_index), 1))
            row_index += 1

        # Add skills
        table_data.append([Paragraph("Skills", self.PARAGRAPH_STYLES["section"])])
        self._append_section_table_style(table_styles, row_index)
        row_index += 1

        for skill in data["skills"]:
            skill_name, skill_description = skill.split(":")
            table_data.append(
                [
                    Paragraph(
                        f"<font name='{self.FONT_NAMES['bold']}'>{skill_name}</font>: {skill_description}",
                        self.PARAGRAPH_STYLES["skills"],
                    )
                ]
            )
            table_styles.extend(
                [
                    ("TOPPADDING", (0, row_index), (1, row_index), 2),
                    ("BOTTOMPADDING", (0, row_index), (1, row_index), 2),
                    ("SPAN", (0, row_index), (1, row_index)),
                ]
            )
            row_index += 1

        table = Table(
            table_data,
            colWidths=[self.FULL_COLUMN_WIDTH * 0.75, self.FULL_COLUMN_WIDTH * 0.3],
            spaceBefore=0,
            spaceAfter=0,
        )
        table.setStyle(TableStyle(table_styles))

        doc.build([table])