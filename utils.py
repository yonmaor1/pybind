from PyPDF2 import PdfReader, PdfWriter, PageObject, Transformation

def rescale_pdf(input_path, target_size, output_path=None):
    """
    Rescales the pages of a PDF to a given size while maintaining the aspect ratio.

    Args:
        input_path (str): Path to the input PDF file.
        target_size (tuple): Target page size as (width, height) in points.
        output_path (str): Path to save the rescaled PDF file (optional).
    """
    target_width, target_height = target_size
    input_pdf = PdfReader(open(input_path, "rb"))
    output_pdf = PdfWriter()

    first_page = input_pdf.pages[0]
    # Get the original page dimensions
    original_width = first_page.mediabox.width
    original_height = first_page.mediabox.height

    # Calculate the scaling factor to maintain aspect ratio
    scale_width = target_width / original_width
    scale_height = target_height / original_height
    scale_factor = min(scale_width, scale_height)  # Choose the smaller scale to avoid overflow

    # Apply the scaling transformation
    # transformation = Transformation().scale(sx=scale_factor, sy=scale_factor)
    print(scale_factor)
    transformation = Transformation().scale(sx=1.2, sy=1.2)

    # Translate the content to center it on the new page
    translate_x = (target_width - (original_width * scale_factor)) / 2
    translate_y = (target_height - (original_height * scale_factor)) / 2
    # transformation = transformation.translate(tx=translate_x, ty=translate_y)

    for page in input_pdf.pages:

        # Create a new blank page with the target dimensions
        new_page = PageObject.create_blank_page(width=target_width, height=target_height)

        # Merge the transformed page onto the new blank page
        new_page.merge_page(page)

        # Apply the transformation to the page
        new_page.add_transformation(transformation)


        # Add the new page to the output PDF
        output_pdf.add_page(new_page)

    # Save the rescaled PDF if an output path is provided
    if output_path:
        with open(output_path, "wb") as output_file:
            output_pdf.write(output_file)

    return output_pdf
def flatten_pdf(input_path, output_path):
    # Read the input PDF
    input_pdf = PdfReader(open(input_path, "rb"))
    flattened_pdf = PdfWriter()

    for page in input_pdf.pages:
        # Create a new blank page with the same dimensions as the original page
        flattened_page = PageObject.create_blank_page(
            width=page.mediabox.width,
            height=page.mediabox.height
        )
        # Merge the original page into the blank page (clipping content outside the bounds)
        flattened_page.merge_page(page)
        # Add the flattened page to the new PDF
        flattened_pdf.add_page(flattened_page)

    # Save the flattened PDF
    with open(output_path, "wb") as output_file:
        flattened_pdf.write(output_file)


import os
from PyPDF2 import PdfReader, PdfWriter

def merge_pdfs_from_directory(directory_path, output_path):
    """
    Merges all PDFs in a directory into a single PDF in alphabetical order of their filenames.

    Args:
        directory_path (str): Path to the directory containing the PDF files.
        output_path (str): Path to save the merged PDF file.
    """
    # Get a list of all PDF files in the directory, sorted alphabetically
    pdf_files = sorted(
        [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
    )

    pdf_order = [int(f.split("-")[0]) for f in pdf_files]

    pdfs = {}

    for i, pdf in zip(pdf_order, pdf_files):
        pdfs[i] = pdf

    sorted_pdfs = sorted(pdfs.items(), key=lambda x: x[0])

    print(sorted_pdfs)


    # Initialize a PdfWriter to create the merged PDF
    merged_pdf = PdfWriter()

    for _, pdf_file in sorted_pdfs:
        pdf_path = os.path.join(directory_path, pdf_file)
        pdf_reader = PdfReader(open(pdf_path, "rb"))

        # Add all pages of the current PDF to the merged PDF
        for page in pdf_reader.pages:
            merged_pdf.add_page(page)

    # Save the merged PDF to the specified output path
    with open(output_path, "wb") as output_file:
        merged_pdf.write(output_file)

    print(f"Merged PDF saved to {output_path}")

if __name__ == "__main__":
    merge_pdfs_from_directory("/Users/yon/Desktop/thr-print", "/Users/yon/Desktop/thr-print/thr.pdf")