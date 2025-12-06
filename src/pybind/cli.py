"""
Main CLI entry point for pybind tools
"""

import click
from .booklet import booklet_command
from .clean_pdf import clean_pdf_command
from .resize_pdf import resize_pdf_command


@click.group()
@click.version_option()
def main():
    """
    pybind - PDF manipulation tools
    
    A collection of tools for PDF manipulation including booklet creation,
    text cleaning, and page resizing.
    """
    pass


# Add subcommands
main.add_command(booklet_command, name="booklet")
main.add_command(clean_pdf_command, name="clean-pdf")
main.add_command(resize_pdf_command, name="resize-pdf")


if __name__ == "__main__":
    main()
