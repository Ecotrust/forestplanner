import os
from pdfjinja import PdfJinja


def fill_pdf(pdf_template, fields_to_fill, outfile):
    """Populates a PDF template with fields specified by user and writes the
    filled PDF to disk. Field names should be defined in the pdf_template.

    Parameters
    ----------
    pdf_template : str, path to file
      path to the template PDF
    fields_to_fill : dict
      fields to populate and the values to populate them with
    outfile : str, path to file
      path to the PDF output file that will be generated

    Returns
    -------
    outfile : str
      if output file successfully created, returns path to that file

    Raises
    ------
    FileNotFoundError
      if output file is not generated
    """
    template = PdfJinja(pdf_template)
    filled = template(fields_to_fill)
    filled.write(open(outfile, 'wb'))

    if os.path.exists(outfile):
        return outfile
    else:
        raise FileNotFoundError('Failed to produce output file.')
