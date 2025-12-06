"""
PDF Page Resizer

This module resizes all pages of a PDF to a specified paper size by:
1. Scaling the width to match the target width
2. Trimming the height from the bottom to match the target height
"""

import sys
from pathlib import Path
import click

try:
    from PyPDF2 import PdfReader, PdfWriter
    from PyPDF2.generic import RectangleObject
except ImportError:
    click.echo("Error: PyPDF2 is required. Install it with: pip install PyPDF2", err=True)
    sys.exit(1)


# Standard paper sizes in points (1 inch = 72 points)
PAPER_SIZES = {
    'A4': (595.28, 841.89),
    'A3': (841.89, 1190.55),
    'A5': (419.53, 595.28),
    'LETTER': (612, 792),
    'LEGAL': (612, 1008),
    'TABLOID': (792, 1224),
}


def inches_to_points(inches):
    """Convert inches to points (1 inch = 72 points)"""
    return inches * 72


def resize_page(page, target_width, target_height, page_num, total_pages):
    """
    Resize a PDF page to target dimensions by:
    1. Scaling width to match target width
    2. Trimming height from bottom to match target height
    
    Returns a dictionary with processing statistics
    """
    # Get current page dimensions
    current_box = page.mediabox
    current_width = float(current_box.width)
    current_height = float(current_box.height)
    
    # Calculate scale factor based on width
    scale_factor = target_width / current_width
    
    # Calculate new height after scaling
    scaled_height = current_height * scale_factor
    
    # Scale the page
    page.scale(scale_factor, scale_factor)
    
    # Track trimming
    trimmed = False
    trim_amount = 0
    
    # If scaled height is greater than target, trim from bottom
    if scaled_height > target_height:
        # Calculate how much to trim from bottom
        trim_amount = scaled_height - target_height
        
        # Get the current mediabox after scaling
        mediabox = page.mediabox
        
        # Convert all values to float to avoid FloatObject arithmetic issues
        left = float(mediabox.lower_left[0])
        bottom = float(mediabox.lower_left[1])
        right = float(mediabox.upper_right[0])
        top = float(mediabox.upper_right[1])
        
        # Trim from bottom by adjusting the lower bound
        new_mediabox = RectangleObject([
            left,                    # left
            bottom + trim_amount,    # bottom (trim from bottom)
            right,                   # right
            top                      # top
        ])
        
        page.mediabox = new_mediabox
        trimmed = True
    
    # Print progress (will be overwritten)
    status = f"Processing page {page_num}/{total_pages}"
    if trimmed:
        status += f" (trimmed {trim_amount:.1f}pt from bottom)"
    click.echo(f"\r{status}", nl=False)
    
    return {
        'original_size': (current_width, current_height),
        'scale_factor': scale_factor,
        'trimmed': trimmed,
        'trim_amount': trim_amount
    }


@click.command()
@click.argument('input_pdf')
@click.argument('output_pdf')
@click.option('--paper-size', 
              type=click.Choice(list(PAPER_SIZES.keys()), case_sensitive=False),
              help='Standard paper size (A4, LETTER, etc.)')
@click.option('--width', type=float, help='Width in inches')
@click.option('--height', type=float, help='Height in inches')
def resize_pdf_command(input_pdf, output_pdf, paper_size, width, height):
    """
    Resize PDF pages to a specified paper size.
    
    You must specify either --paper-size or both --width and --height.
    
    Examples:
    
      pybind resize-pdf input.pdf output.pdf --paper-size A4
      
      pybind resize-pdf input.pdf output.pdf --paper-size LETTER
      
      pybind resize-pdf input.pdf output.pdf --width 8.5 --height 11
    
    Available paper sizes: A4, A3, A5, LETTER, LEGAL, TABLOID
    """
    
    # Validate input file
    input_path = Path(input_pdf)
    if not input_path.exists():
        click.echo(f"Error: Input file '{input_pdf}' does not exist", err=True)
        raise click.Abort()
    
    # Get target dimensions
    if paper_size:
        target_width, target_height = PAPER_SIZES[paper_size.upper()]
    elif width and height:
        target_width, target_height = inches_to_points(width), inches_to_points(height)
    else:
        click.echo("Error: You must specify either --paper-size or both --width and --height", err=True)
        raise click.Abort()
    
    click.echo(f"Input file: {input_pdf}")
    click.echo(f"Output file: {output_pdf}")
    click.echo(f"Target size: {target_width:.1f} x {target_height:.1f} points")
    click.echo()
    
    try:
        # Read the input PDF
        reader = PdfReader(input_pdf)
        writer = PdfWriter()
        
        total_pages = len(reader.pages)
        click.echo(f"Processing {total_pages} pages...")
        
        # Track statistics
        stats = []
        
        # Process each page
        for i, page in enumerate(reader.pages, 1):
            page_stats = resize_page(page, target_width, target_height, i, total_pages)
            stats.append(page_stats)
            writer.add_page(page)
        
        # Clear the progress line
        click.echo("\r" + " " * 80 + "\r", nl=False)
        
        # Write the output PDF
        with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)
        
        click.echo(f"Successfully created resized PDF: {output_pdf}")
        
    except Exception as e:
        click.echo(f"Error processing PDF: {e}", err=True)
        raise click.Abort()
