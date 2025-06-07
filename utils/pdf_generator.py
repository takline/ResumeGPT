"""
Alternative PDF generation utility using LaTeX (via latexmk) and Jinja2 templating.

Note: This module appears to be a potentially legacy or alternative PDF generation
method not currently integrated with the main `ResumeImprover` workflow, which uses
the ReportLab-based generator in the `pdf_generation` directory.

This generator takes YAML data and a LaTeX template (Jinja2 compatible) to produce
a PDF. It requires a functional LaTeX distribution (with `latexmk` and necessary
packages like `几何学` (geometry), `fontspec`, etc.) to be installed on the system
and accessible in the system's PATH.
"""
import os
import subprocess
import logging # Use logging instead of direct config.logger for module-level logger
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from .. import config # For PROJECT_PATH if needed for templates
from . import yaml_handler # Uses the project's standard YAML handler (PyYAML based)

logger = logging.getLogger(__name__)

def generate_pdf(yaml_file_path: str, template_filename: str = "resume.tex") -> str:
    """
    Generates a PDF from a YAML data file using a LaTeX Jinja2 template.

    This function reads data from the specified YAML file, renders it into a
    LaTeX (.tex) file using the specified Jinja2 template, and then compiles
    the .tex file into a PDF using `latexmk`.

    Args:
        yaml_file_path (str): Absolute path to the input YAML data file.
        template_filename (str): Filename of the LaTeX template (e.g., "resume.tex").
                                 This template is expected to be in a 'templates' directory
                                 located at the project root (`config.PROJECT_PATH`).

    Returns:
        str: Absolute path to the generated PDF file.

    Raises:
        FileNotFoundError: If the YAML file, template file, or 'templates' directory is not found,
                           or if `latexmk` command is not found (indicating LaTeX not installed/in PATH).
        ValueError: If PDF generation fails (e.g., `latexmk` error, YAML data issues).
        Exception: For other unexpected errors during the process.
    """
    if not os.path.isabs(yaml_file_path):
        msg = f"YAML file path must be absolute: {yaml_file_path}"
        logger.error(msg)
        raise ValueError(msg)
    if not os.path.isfile(yaml_file_path):
        msg = f"YAML input file not found: {yaml_file_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    # Determine directory and base filename for output files
    output_dir, yaml_basename = os.path.split(yaml_file_path)
    base_filename_no_ext, _ = os.path.splitext(yaml_basename)

    # Define .tex and final .pdf output paths in the same directory as the YAML file
    tex_output_path = os.path.join(output_dir, f"{base_filename_no_ext}.tex")
    final_pdf_path = os.path.join(output_dir, f"{base_filename_no_ext}.pdf")

    # Load YAML data
    try:
        yaml_data = yaml_handler.read_yaml(filename=yaml_file_path)
        if yaml_data is None: # read_yaml might return None on some errors
            raise ValueError(f"Could not load or parse data from YAML file: {yaml_file_path}")
    except Exception as e: # Catch errors from read_yaml more broadly
        logger.error(f"Error reading YAML file {yaml_file_path}: {e}", exc_info=True)
        raise

    # Set up Jinja2 environment
    template_dir = os.path.join(config.PROJECT_PATH, "templates")
    if not os.path.isdir(template_dir):
        msg = f"Jinja2 template directory not found at: {template_dir}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="\\VAR{",
        variable_end_string="}",
        comment_start_string="\\#{",
        comment_end_string="}",
        line_statement_prefix="%%",
        line_comment_prefix="%#",
        autoescape=False,
    )

    try:
        template = env.get_template(template_filename)
    except TemplateNotFound as e:
        logger.error(f"Jinja2 template '{template_filename}' not found in {template_dir}: {e}", exc_info=True)
        raise FileNotFoundError(f"Jinja2 template '{template_filename}' not found in {template_dir}.") from e
    except Exception as e: # Other Jinja errors
        logger.error(f"Error loading Jinja2 template '{template_filename}': {e}", exc_info=True)
        raise

    # Render the LaTeX string
    try:
        latex_string = template.render(**yaml_data)
    except Exception as e:
        logger.error(f"Error rendering LaTeX template '{template_filename}' with data from {yaml_file_path}: {e}", exc_info=True)
        raise ValueError(f"Failed to render LaTeX template: {e}") from e

    try:
        # Write the rendered LaTeX to a .tex file
        with open(tex_output_path, "w", encoding="utf-8") as tex_file:
            tex_file.write(latex_string)
        logger.info(f"Temporary LaTeX file written to: {tex_output_path}")

        # Compile .tex to .pdf using latexmk
        latexmk_jobname = os.path.join(output_dir, f"latexmk_temp_{base_filename_no_ext}")

        compile_cmd = [
            "latexmk", "-pdf", "-interaction=nonstopmode",
            f"-jobname={latexmk_jobname}", tex_output_path,
        ]

        logger.info(f"Running latexmk: {' '.join(compile_cmd)}")
        process_result = subprocess.run(
            compile_cmd, cwd=output_dir, capture_output=True, text=True, check=False
        )

        latexmk_pdf_output = f"{latexmk_jobname}.pdf"

        if process_result.returncode == 0 and os.path.isfile(latexmk_pdf_output):
            if os.path.exists(final_pdf_path): # Remove existing final PDF to avoid os.rename error on some OS
                os.remove(final_pdf_path)
            os.rename(latexmk_pdf_output, final_pdf_path)
            logger.info(f"PDF generated successfully: {final_pdf_path}")

            # Clean up auxiliary LaTeX files
            cleanup_cmd = ["latexmk", "-c", f"-jobname={latexmk_jobname}"] # No need to specify .tex file for -c with jobname
            subprocess.run(cleanup_cmd, cwd=output_dir, capture_output=True, text=True, check=False)
            logger.info(f"Cleaned up auxiliary LaTeX files for jobname: {os.path.basename(latexmk_jobname)}.")
            # Explicitly remove the .tex file we created
            if os.path.exists(tex_output_path):
                os.remove(tex_output_path)
        else:
            error_message = f"PDF generation failed. latexmk exited with code {process_result.returncode}."
            logger.error(error_message)
            logger.error(f"latexmk stdout:\n{process_result.stdout}")
            logger.error(f"latexmk stderr:\n{process_result.stderr}")
            log_file = f"{latexmk_jobname}.log"
            if os.path.exists(log_file): # Check if log file exists before trying to read
                try:
                    with open(log_file, "r", encoding="utf-8") as lf:
                        logger.error(f"latexmk log ({log_file}):\n{lf.read(2000)}") # Log first 2000 chars
                except Exception as log_e:
                    logger.error(f"Could not read latexmk log file {log_file}: {log_e}")
            else:
                 logger.error(f"latexmk log file not found at expected path: {log_file}")
            raise ValueError(error_message) # Raise a more generic error

    except FileNotFoundError as e:
        logger.error(f"Failed to generate PDF: `latexmk` command not found. Ensure LaTeX is installed and in PATH. Error: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during PDF generation pipeline: {e}", exc_info=True)
        raise

    return final_pdf_path
