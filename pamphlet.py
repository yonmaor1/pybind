from PyPDF2 import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.lib.pagesizes import A4, LETTER
from utils import flatten_pdf, rescale_pdf
import io
import os
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Create a booklet from a PDF file.")
    parser.add_argument("-i", "--input", required=True, help="Input PDF file path")
    parser.add_argument("-o", "--output", default="out.pdf", help="Output PDF file path")
    parser.add_argument("-p", "--page-size", default="LETTER", help="Page size of the input/output PDF")
    parser.add_argument("-s", "--scale", default=1, help="Scale factor for the booklet pages")
    parser.add_argument("-S", "--spread-layout", action="store_true", help="Indicates that the input PDF is organized into spreads")
    return parser.parse_args()

def open_pdf(input_path):
    return PdfReader(open(input_path, "rb"))

def save_pdf(pdf_writer, output_path):
    with open(output_path, "wb") as output_file:
        pdf_writer.write(output_file)

def spread_to_pages(input_pdf):
    # Read the input PDF
    spread_pdf = PdfWriter()

    for page in input_pdf.pages:
        # Duplicate each page
        left_page = PageObject.create_blank_page(width=page.mediabox.width / 2, height=page.mediabox.height)
        right_page = PageObject.create_blank_page(width=page.mediabox.width / 2, height=page.mediabox.height)

        # Crop the left half
        left_page.merge_page(page)
        left_page.mediabox.upper_right = (page.mediabox.width / 2, page.mediabox.upper_right[1])

        # Crop the right half
        right_page.merge_page(page)
        right_page.add_transformation(Transformation().translate(tx=-page.mediabox.width / 2, ty=0))

        # Add the cropped pages to the new PDF
        spread_pdf.add_page(left_page)
        spread_pdf.add_page(right_page)

    # Save the processed spread layout to a temporary file
    with open("pages.pdf", "wb") as output_file:
        spread_pdf.write(output_file)

    # flatten_pdf(tmp_spread_path, tmp_spread_path)

    return spread_pdf

def create_booklet(input_pdf, page_size=LETTER, scale=1, spread_layout=False):

    num_pages = len(input_pdf.pages)
    # flatten_pdf(input_path, input_path)
    # Add a blank page if the number of pages is odd

    tmp_pdf = PdfWriter()
    for _, page in enumerate(input_pdf.pages):
        # print(_)
        tmp_pdf.add_page(page)
    
    if num_pages % 2 != 0:
        blank_page = PageObject.create_blank_page(width=page_size[0], height=page_size[1])
        tmp_pdf.add_page(blank_page)
        num_pages += 1

    # DEBUG     
    # tmp_path = input_path.split(".")[0] + "_tmp.pdf"
    # with open(tmp_path, "wb") as output_file:
    #     tmp_pdf.write(output_file)
    
    booklet_pages = num_pages // 2

    booklet_dims = (scale * 0.6 * page_size[0], scale * 0.6 * page_size[1])
    if (spread_layout):
        booklet_dims = (scale * page_size[0], scale * page_size[1])

    # DEBUG
    # print(f"Booklet dimensions: {booklet_dims}")
    # print(f"Page dimensions: {page_size}")
    # print((page_size[0] - booklet_dims[1]) / 2)

    # Create a new PDF for the booklet
    output_pdf = PdfWriter()

    for i in range(booklet_pages):
        # Create a new blank page in landscape mode
        new_page = PageObject.create_blank_page(width=page_size[1], height=page_size[0])
        
        # Draw the right page
        right_page = tmp_pdf.pages[i]
        if (not spread_layout): 
            right_page.add_transformation(Transformation().scale(scale * 0.6, scale * 0.6))
            new_page.add_transformation(Transformation().translate(page_size[1] / 2, int((page_size[0] - booklet_dims[1]) / 2) ))
        
        if i % 2 == 0:
            right_page.add_transformation(Transformation().scale(-1, 1).translate(page_size[1]/2, 0))
        
        new_page.merge_page(right_page, expand=False)
        if (spread_layout):
            new_page.add_transformation(Transformation().translate(page_size[1] / 2, 0))

        # Draw the left page
        left_page = tmp_pdf.pages[num_pages - i - 1]
        if (not spread_layout): 
            left_page.add_transformation(Transformation().scale(scale * 0.6, scale * 0.6))

        if i % 2 == 0:
            left_page.add_transformation(Transformation().scale(-1, 1).translate(page_size[1]/2, 0))
    
        new_page.merge_page(left_page, expand=False)
        left_page.add_transformation(Transformation().translate(0, int((page_size[0] - booklet_dims[1]) / 2) ))

        # Add the new page to the output PDF

        if i % 2 == 0:
            new_page.add_transformation(Transformation().scale(1, -1).translate(0, page_size[0]))
        output_pdf.add_page(new_page)

    return output_pdf

def main():
    args = parse_arguments()
    input_path = args.input
    output_path = args.output
    page_sizes = {
        "LETTER": LETTER,
        "A4": A4,
        "TABLOID": (LETTER[1], 2 * LETTER[0]), 
    }

    print(f"Converting {input_path} to a pamphlet, and saving to {output_path}")
    print(f"with page size {args.page_size} and scale {args.scale}")
    if (args.spread_layout):
        print("Input PDF is in spread layout, processing accordingly.")

    page_size = page_sizes[args.page_size]

    scale = float(args.scale)
    if scale < 0 or scale > 1:
        raise ValueError("Scale factor must be between 0 and 1")

    if args.spread_layout:
        # tmp_spread_path = input_path.split(".")[0] + "_spread_tmp.pdf"
        input_pdf = PdfReader(open(input_path, "rb"))
        page_layout = spread_to_pages(input_pdf)
        booklet = create_booklet(page_layout, page_size=page_size, scale=scale, spread_layout=args.spread_layout)
        save_pdf(booklet, output_path)
    else:
        input_pdf = PdfReader(open(input_path, "rb"))
        booklet = create_booklet(input_pdf, page_size=page_size, scale=scale)
        save_pdf(booklet, output_path)

if __name__ == "__main__":
    main()