"""
Booklet creation functionality - converts PDF to booklet format
"""

import os
import click
from PyPDF2 import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.lib.pagesizes import A4, LETTER


def create_booklet(input_path, output_path, page_size=LETTER, scale=1):
    """Create a booklet from a PDF file."""
    # Read the input PDF
    input_pdf = PdfReader(open(input_path, "rb"))
    num_pages = len(input_pdf.pages)
    # Add a blank page if the number of pages is odd
    tmp_pdf = PdfWriter()
    for page in input_pdf.pages:
        tmp_pdf.add_page(page)
    
    if num_pages % 2 != 0:
        blank_page = PageObject.create_blank_page(width=page_size[0], height=page_size[1])
        tmp_pdf.add_page(blank_page)
        num_pages += 1
        
    tmp_path = input_path.split(".")[0] + "_tmp.pdf"
    with open(tmp_path, "wb") as output_file:
        tmp_pdf.write(output_file)
    
    booklet_pages = num_pages // 2

    booklet_dims = (scale * 0.6 * page_size[0], scale * 0.6 * page_size[1])

    print(f"Booklet dimensions: {booklet_dims}")
    print(f"Page dimensions: {page_size}")
    print((page_size[0] - booklet_dims[1]) / 2)

    # Create a new PDF for the booklet
    output_pdf = PdfWriter()

    # Calculate the number of pages in the booklet

    for i in range(booklet_pages):
        # Create a new blank page in landscape mode
        new_page = PageObject.create_blank_page(width=page_size[1], height=page_size[0])
        
        # Draw the right page
        right_page = tmp_pdf.pages[i]
        right_page.add_transformation(Transformation().scale(scale * 0.6, scale * 0.6))
        new_page.merge_page(right_page, expand=False)
        new_page.add_transformation(Transformation().translate(page_size[1] / 2, int((page_size[0] - booklet_dims[1]) / 2) ))

        # Draw the left page
        left_page = tmp_pdf.pages[num_pages - i - 1]
        left_page.add_transformation(Transformation().scale(scale * 0.6, scale * 0.6).translate(0, int((page_size[0] - booklet_dims[1]) / 2) ))
        new_page.merge_page(left_page, expand=False)


        # Add the new page to the output PDF
        output_pdf.add_page(new_page)

    # Save the output PDF
    with open(output_path, "wb") as output_file:
        output_pdf.write(output_file)

    # Delete the temporary PDF file
    os.remove(tmp_path)


@click.command()
@click.option("-i", "--input", "input_path", required=True, 
              help="Input PDF file path")
@click.option("-o", "--output", "output_path", default="out.pdf", 
              help="Output PDF file path")
@click.option("-p", "--page-size", default="LETTER", 
              type=click.Choice(["LETTER", "A4"], case_sensitive=False),
              help="Page size of the input/output PDF")
@click.option("-s", "--scale", default=1.0, type=float,
              help="Scale factor for the booklet pages")
def booklet_command(input_path, output_path, page_size, scale):
    """Create a booklet from a PDF file."""
    
    if not os.path.exists(input_path):
        click.echo(f"Error: Input file '{input_path}' does not exist", err=True)
        raise click.Abort()
    
    page_sizes = {
        "LETTER": LETTER,
        "A4": A4
    }

    page_size_tuple = page_sizes[page_size.upper()]

    if scale < 0 or scale > 1:
        click.echo("Error: Scale factor must be between 0 and 1", err=True)
        raise click.Abort()

    try:
        create_booklet(input_path, output_path, page_size_tuple, scale)
        click.echo(f"Successfully created booklet: {output_path}")
    except Exception as e:
        click.echo(f"Error creating booklet: {e}", err=True)
        raise click.Abort()
