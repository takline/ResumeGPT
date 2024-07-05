import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO
from ruamel.yaml.error import YAMLError
from .. import config
from . import yaml_handler


def generate_pdf(yaml_file: str, template_file: str = None) -> str:
    """
    Generates a PDF from a YAML file using a LaTeX template.

    Args:
        yaml_file (str): Path to the YAML file.
        template_file (str): Path to the LaTeX template file.

    Returns:
        str: Path to the generated PDF file.
    """
    # set default template file. file location is relative to `templates` directory
    if not template_file:
        template_file = "resume.tex"

    dirname, basename = os.path.split(yaml_file)
    filename, ext = os.path.splitext(basename)
    filename = os.path.join(dirname, filename)

    yaml_data = yaml_handler.read_yaml(filename=yaml_file)

    # Set up jinja environment and template
    env = Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        block_start_string="\BLOCK{",
        block_end_string="}",
        variable_start_string="\VAR{",
        variable_end_string="}",
        comment_start_string="\#{",
        comment_end_string="}",
        line_statement_prefix="%%",
        line_comment_prefix="%#",
        autoescape=False,
        loader=FileSystemLoader("templates"),
    )
    template = env.get_template(template_file)

    latex_string = template.render(**yaml_data)

    try:
        with open(f"{filename}.tex", "wt") as stream:
            stream.write(latex_string)

        # convert to pdf and clean up temp files
        jobname = os.path.join(dirname, "latexmk_temp")
        cmd = subprocess.run(
            [
                "latexmk",
                "-pdf",
                f"-jobname={jobname}",
                f"{filename}.tex",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # rename pdf
        if os.path.isfile(f"{jobname}.pdf"):
            os.rename(f"{jobname}.pdf", f"{filename}.pdf")
            cmd = subprocess.run(
                [
                    "latexmk",
                    "-c",
                    f"-jobname={jobname}",
                    f"{filename}.tex",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            message = f"PDF could not be generated. See latexmk logs {jobname}.log"
            config.logger.error(message)
            raise ValueError(message)
    except Exception as e:
        config.logger.error(f"Failed to generate PDF: {e}")
        raise e

    return f"{filename}.pdf"
