# pybind - PDF Manipulation Tools

Command-line tools for book binders

## Features

- **Booklet Creation**: Convert regular PDFs into booklet format for printing and folding
- **PDF Text Cleaning**: Clean PDF text while preserving exact layout, positioning, and formatting
- **PDF Page Resizing**: Resize PDF pages to standard paper sizes with intelligent scaling and trimming

## Installation

### Using uv (recommended)

```bash
git clone <repository-url>
cd pybind
uv tool install . -e
```

### Using pip

```bash
git clone <repository-url>
cd pybind
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Usage

After installation, you can use the `pybind` command with various subcommands:

### Booklet Creation

Convert a PDF into booklet format for printing:

```bash
pybind booklet -i input.pdf -o booklet.pdf
```

Options:
- `-i, --input`: Input PDF file path (required)
- `-o, --output`: Output PDF file path (default: out.pdf)
- `-p, --page-size`: Page size - LETTER or A4 (default: LETTER)
- `-s, --scale`: Scale factor for booklet pages (default: 1.0, range: 0.0-1.0)

Example:
```bash
pybind booklet -i document.pdf -o my_booklet.pdf --page-size A4 --scale 0.8
```

### PDF Text Cleaning

Clean PDF text while preserving exact layout and positioning:

```bash
pybind clean-pdf input.pdf output.pdf
```

Options:
- `--font`: Base font family to use (default: Times-Roman)

Available fonts: Times-Roman, Helvetica, Courier

This tool preserves:
- Exact text positioning
- Page dimensions
- Line spacing
- Font sizes
- Bold/italic formatting (mapped to clean fonts)

Example:
```bash
pybind clean-pdf messy.pdf clean.pdf --font Helvetica
```

### PDF Page Resizing

Resize PDF pages to standard paper sizes:

```bash
pybind resize-pdf input.pdf output.pdf --paper-size A4
```

Options:
- `--paper-size`: Standard paper size (A4, A3, A5, LETTER, LEGAL, TABLOID)
- `--width`: Custom width in inches
- `--height`: Custom height in inches

You must specify either `--paper-size` or both `--width` and `--height`.

Examples:
```bash
# Using standard paper size
pybind resize-pdf input.pdf output.pdf --paper-size LETTER

# Using custom dimensions
pybind resize-pdf input.pdf output.pdf --width 8.5 --height 11
```

## Dependencies

- **PyPDF2**: PDF manipulation
- **reportlab**: PDF generation and layout
- **PyMuPDF (fitz)**: Advanced PDF text extraction and manipulation
- **click**: Command-line interface

## Development

### Project Structure

```
pybind/
├── src/pybind/
│   ├── __init__.py
│   ├── cli.py          # Main CLI entry point
│   ├── booklet.py      # Booklet creation functionality
│   ├── clean_pdf.py    # PDF text cleaning
│   └── resize_pdf.py   # PDF page resizing
├── pyproject.toml      # Project configuration
└── README.md
```

### Running Tests

```bash
# Install development dependencies
uv sync --dev

# Run tests (when available)
pytest
```

### Code Formatting

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## Examples

The `examples/` directory contains sample PDFs and outputs to demonstrate the tools' capabilities.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed
2. **Permission errors**: Ensure you have write permissions to the output directory
3. **Font issues**: If custom fonts don't work, stick to the built-in fonts (Times-Roman, Helvetica, Courier)

### Getting Help

Use the `--help` flag with any command to see detailed usage information:

```bash
pybind --help
pybind booklet --help
pybind clean-pdf --help
pybind resize-pdf --help
```
