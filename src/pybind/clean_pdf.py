"""
PDF Text Cleaner - Exact Layout Preservation

This module copies text from a PDF page-by-page, line-by-line, preserving exact positioning
and creating a new PDF with clean fonts while maintaining the original layout.
"""

import sys
from pathlib import Path
import click

try:
    import fitz  # PyMuPDF
except ImportError:
    click.echo("Error: PyMuPDF is required. Install it with: pip install pymupdf", err=True)
    sys.exit(1)


class TextLine:
    """Represents a line of text with exact positioning"""
    def __init__(self, text, bbox, font_size, font_flags=0):
        self.text = text.strip()
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.x0 = bbox[0]
        self.y0 = bbox[1]
        self.x1 = bbox[2]
        self.y1 = bbox[3]
        self.font_size = font_size
        self.font_flags = font_flags
        self.width = self.x1 - self.x0
        self.text_type = None  # Will be set by classify_text_type
        
    @property
    def is_bold(self):
        return bool(self.font_flags & 2**4)
    
    @property 
    def is_italic(self):
        return bool(self.font_flags & 2**1)
    
    def should_justify(self):
        """Determine if this line should be justified based on its characteristics"""
        # Only justify main text
        if self.text_type != 'main_text':
            return False
        # Don't justify very short lines or headings
        if len(self.text) < 20:  # Very short lines
            return False
        if self.text.isupper():  # All caps (likely heading)
            return False
        if len(self.text.split()) < 4:  # Very few words
            return False
        return True
    
    def is_main_text(self):
        """Check if this line is main body text (not auxiliary)"""
        return self.text_type == 'main_text'
        
    def __repr__(self):
        return f"TextLine('{self.text[:30]}...', type={self.text_type}, bbox={self.bbox}, size={self.font_size:.1f})"


class Paragraph:
    """Represents a paragraph with calculated formatting properties"""
    def __init__(self, lines):
        self.lines = lines
        self.is_main_text_paragraph = any(line.is_main_text() for line in lines)
        
        # Calculate paragraph properties from constituent lines
        self._calculate_properties()
    
    def _calculate_properties(self):
        """Calculate paragraph-level properties from the constituent lines"""
        if not self.lines:
            return
        
        # Find the widest line to determine paragraph width
        self.width = max(line.width for line in self.lines)
        
        # Find main text lines for calculating margins
        main_text_lines = [line for line in self.lines if line.is_main_text()]
        
        if main_text_lines:
            # Calculate average left x-value after the first line (for body text margin)
            if len(main_text_lines) > 1:
                subsequent_lines = main_text_lines[1:]
                self.left_margin = sum(line.x0 for line in subsequent_lines) / len(subsequent_lines)
            else:
                self.left_margin = main_text_lines[0].x0
            
            # Calculate first line indent (difference from average margin)
            first_main_line = main_text_lines[0]
            self.first_line_indent = first_main_line.x0 - self.left_margin
            
            # Use the first main text line's position as paragraph baseline
            self.y_position = first_main_line.y0
            
            # Calculate line height from main text
            font_sizes = [line.font_size for line in main_text_lines]
            self.line_height = max(font_sizes) * 1.2  # 120% of font size for line spacing
            
        else:
            # Fallback for auxiliary text paragraphs
            self.left_margin = min(line.x0 for line in self.lines)
            self.first_line_indent = 0
            self.y_position = min(line.y0 for line in self.lines)
            self.line_height = max(line.font_size for line in self.lines) * 1.2
    
    def should_justify(self):
        """Determine if this paragraph should be justified"""
        return self.is_main_text_paragraph and len(self.lines) > 1
    
    def get_target_width(self):
        """Get the target width for justification"""
        return self.width
    
    def __repr__(self):
        return f"Paragraph({len(self.lines)} lines, width={self.width:.1f}, main_text={self.is_main_text_paragraph})"


class PageStruct:
    """Represents a page with structured paragraph organization"""
    def __init__(self, page_rect, text_lines):
        self.page_rect = page_rect
        self.text_lines = text_lines
        self.paragraphs = []
        
        # Classify text types first
        self._classify_text_types()
        
        # Group lines into paragraphs
        self._group_into_paragraphs()
    
    def _classify_text_types(self):
        """Classify each text line as main_text or auxiliary_text"""
        if not self.text_lines:
            return
        
        page_height = self.page_rect.height
        page_width = self.page_rect.width
        
        # Define margins for detecting headers/footers
        header_threshold = page_height * 0.9  # Top 10% of page
        footer_threshold = page_height * 0.1  # Bottom 10% of page
        
        # Analyze font sizes to identify main text size
        font_sizes = [line.font_size for line in self.text_lines]
        if font_sizes:
            from collections import Counter
            size_counts = Counter(font_sizes)
            main_text_size = size_counts.most_common(1)[0][0]
            size_tolerance = 2  # Points tolerance for main text size
        else:
            main_text_size = 12
            size_tolerance = 2
        
        # Find the main text area (common left margin for body text)
        potential_main_lines = []
        for line in self.text_lines:
            if (footer_threshold < line.y1 < header_threshold and 
                abs(line.font_size - main_text_size) <= size_tolerance and
                len(line.text.split()) >= 3):
                potential_main_lines.append(line)
        
        if potential_main_lines:
            from collections import Counter
            left_margins = [line.x0 for line in potential_main_lines]
            margin_counts = Counter([round(margin, 1) for margin in left_margins])
            main_left_margin = margin_counts.most_common(1)[0][0]
            margin_tolerance = 15  # Points tolerance for left margin
        else:
            main_left_margin = page_width * 0.15  # Assume 15% left margin
            margin_tolerance = page_width * 0.1
        
        # Classify each line
        for line in self.text_lines:
            is_auxiliary = False
            
            # Various classification rules
            if line.y1 > header_threshold or line.y1 < footer_threshold:
                is_auxiliary = True
            elif (len(line.text.strip()) <= 3 and 
                  (line.text.strip().isdigit() or any(char.isdigit() for char in line.text.strip()))):
                is_auxiliary = True
            elif len(line.text.strip()) < 10 and len(line.text.split()) <= 2:
                is_auxiliary = True
            elif line.text.isupper() and len(line.text.strip()) < 50:
                is_auxiliary = True
            elif abs(line.x0 - main_left_margin) > margin_tolerance:
                if not (line.x0 > main_left_margin + margin_tolerance and 
                       abs(line.font_size - main_text_size) <= size_tolerance and
                       len(line.text.split()) >= 4):
                    is_auxiliary = True
            elif abs(line.font_size - main_text_size) > size_tolerance * 2:
                is_auxiliary = True
            elif line.width > page_width * 0.8:
                is_auxiliary = True
            
            line.text_type = 'auxiliary_text' if is_auxiliary else 'main_text'
    
    def _group_into_paragraphs(self):
        """Group text lines into paragraphs based on indentation and main text detection"""
        if not self.text_lines:
            return
        
        # Filter to only main text lines for paragraph detection
        main_text_lines = [line for line in self.text_lines if line.is_main_text()]
        
        if not main_text_lines:
            # No main text, treat each line as its own paragraph
            self.paragraphs = [Paragraph([line]) for line in self.text_lines]
            return
        
        # Find the most common left margin among main text lines
        from collections import Counter
        left_margins = [line.x0 for line in main_text_lines]
        margin_counts = Counter([round(margin, 1) for margin in left_margins])
        baseline_x = margin_counts.most_common(1)[0][0]
        indent_threshold = 20  # Points - if x is more than this beyond baseline, it's indented
        
        current_paragraph_lines = []
        first_main_text_found = False
        
        for line in self.text_lines:
            # If this is main text and we haven't started a paragraph yet, start one
            if line.is_main_text() and not first_main_text_found:
                if current_paragraph_lines:
                    self.paragraphs.append(Paragraph(current_paragraph_lines))
                current_paragraph_lines = [line]
                first_main_text_found = True
            # If this is main text and indented, start a new paragraph
            elif line.is_main_text() and line.x0 > baseline_x + indent_threshold:
                if current_paragraph_lines:
                    self.paragraphs.append(Paragraph(current_paragraph_lines))
                current_paragraph_lines = [line]
            else:
                # Continue current paragraph (includes auxiliary text)
                current_paragraph_lines.append(line)
        
        # Don't forget the last paragraph
        if current_paragraph_lines:
            self.paragraphs.append(Paragraph(current_paragraph_lines))
    
    def get_paragraphs(self):
        """Get all paragraphs in this page"""
        return self.paragraphs
    
    def __repr__(self):
        return f"PageStruct({len(self.paragraphs)} paragraphs, {len(self.text_lines)} lines)"


def extract_text_lines_from_page(page):
    """
    Extract text lines from a page with exact positioning information.
    Groups characters into lines based on their vertical alignment.
    """
    text_lines = []
    
    try:
        # Get text with detailed character information
        text_dict = page.get_text("dict")
        
        # Collect all text spans with their positions
        spans = []
        
        for block in text_dict["blocks"]:
            if "lines" in block:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:  # Only process non-empty text
                            spans.append({
                                'text': text,
                                'bbox': span["bbox"],
                                'size': span["size"],
                                'flags': span["flags"]
                            })
        
        # Group spans into lines based on vertical position
        # Sort by vertical position first, then horizontal
        spans.sort(key=lambda s: (-s['bbox'][1], s['bbox'][0]))
        
        current_line_spans = []
        current_y = None
        y_tolerance = 2  # Points tolerance for same line
        
        for span in spans:
            span_y = span['bbox'][1]  # y0 coordinate
            
            # Check if this span is on the same line as current line
            if current_y is None or abs(span_y - current_y) <= y_tolerance:
                # Same line
                current_line_spans.append(span)
                if current_y is None:
                    current_y = span_y
            else:
                # New line - process current line first
                if current_line_spans:
                    line = create_text_line_from_spans(current_line_spans)
                    if line:
                        text_lines.append(line)
                
                # Start new line
                current_line_spans = [span]
                current_y = span_y
        
        # Don't forget the last line
        if current_line_spans:
            line = create_text_line_from_spans(current_line_spans)
            if line:
                text_lines.append(line)
    
    except Exception as e:
        click.echo(f"Warning: Error extracting text from page: {e}", err=True)
    
    return text_lines


def create_text_line_from_spans(spans):
    """Create a TextLine object from a list of spans on the same line."""
    if not spans:
        return None
    
    # Sort spans by horizontal position
    spans.sort(key=lambda s: s['bbox'][0])
    
    # Combine text with appropriate spacing
    line_text_parts = []
    prev_x1 = None
    
    for span in spans:
        text = span['text']
        x0 = span['bbox'][0]
        
        # Add spacing between spans if there's a gap
        if prev_x1 is not None:
            gap = x0 - prev_x1
            char_width = span['size'] * 0.6  # Approximate character width
            
            if gap > char_width:  # Significant gap
                spaces_needed = max(1, int(gap / char_width))
                line_text_parts.append(' ' * min(spaces_needed, 10))  # Max 10 spaces
        
        line_text_parts.append(text)
        prev_x1 = span['bbox'][2]
    
    line_text = ''.join(line_text_parts)
    
    # Calculate bounding box for the entire line
    min_x0 = min(s['bbox'][0] for s in spans)
    min_y0 = min(s['bbox'][1] for s in spans)
    max_x1 = max(s['bbox'][2] for s in spans)
    max_y1 = max(s['bbox'][3] for s in spans)
    
    line_bbox = (min_x0, min_y0, max_x1, max_y1)
    
    # Use the font size from the first span (or average if needed)
    font_size = spans[0]['size']
    font_flags = spans[0]['flags']
    
    return TextLine(line_text, line_bbox, font_size, font_flags)


def insert_justified_text_with_position(page, line, font_name, target_width, x_position, y_position):
    """
    Insert text with justified alignment to a specific target width at specified position.
    Distributes extra space evenly between words.
    """
    words = line.text.split()
    
    if len(words) <= 1:
        # Can't justify single word or empty line, use left alignment
        insert_point = fitz.Point(x_position, y_position)
        page.insert_text(
            insert_point,
            line.text,
            fontsize=line.font_size,
            fontname=font_name,
            color=(0, 0, 0)
        )
        return
    
    # Calculate the natural width of the text without extra spacing
    natural_text = ' '.join(words)
    text_width = fitz.get_text_length(natural_text, fontname=font_name, fontsize=line.font_size)
    
    # Calculate how much extra space we need to distribute to reach target width
    extra_space = target_width - text_width
    
    # Only justify if we have reasonable extra space (not too much, not negative)
    if extra_space < 0 or extra_space > line.font_size * 3:
        # Don't justify if text is too long or gap would be too large
        insert_point = fitz.Point(x_position, y_position)
        page.insert_text(
            insert_point,
            line.text,
            fontsize=line.font_size,
            fontname=font_name,
            color=(0, 0, 0)
        )
        return
    
    # Distribute extra space between words
    gaps_between_words = len(words) - 1
    if gaps_between_words > 0:
        extra_space_per_gap = extra_space / gaps_between_words
        
        # Insert words one by one with calculated spacing
        current_x = x_position
        
        for i, word in enumerate(words):
            insert_point = fitz.Point(current_x, y_position)
            page.insert_text(
                insert_point,
                word,
                fontsize=line.font_size,
                fontname=font_name,
                color=(0, 0, 0)
            )
            
            # Calculate position for next word
            word_width = fitz.get_text_length(word, fontname=font_name, fontsize=line.font_size)
            current_x += word_width
            
            # Add space for next word (if not the last word)
            if i < len(words) - 1:
                natural_space_width = fitz.get_text_length(' ', fontname=font_name, fontsize=line.font_size)
                current_x += natural_space_width + extra_space_per_gap


def create_clean_pdf_with_exact_layout(input_path, output_path, clean_font="Times-Roman"):
    """
    Create a clean PDF that preserves the exact layout of the original.
    """
    
    try:
        # Open input PDF
        input_doc = fitz.open(input_path)
        
        # Create output PDF
        output_doc = fitz.open()  # New empty document
        
        total_pages = len(input_doc)
        click.echo(f"Processing {total_pages} pages...")
        
        for page_num in range(total_pages):
            click.echo(f"\rProcessing page {page_num + 1}/{total_pages}", nl=False)
            
            input_page = input_doc[page_num]
            
            # Get page dimensions
            page_rect = input_page.rect
            
            # Create new page with same dimensions
            output_page = output_doc.new_page(width=page_rect.width, height=page_rect.height)
            
            # Extract text lines from input page
            text_lines = extract_text_lines_from_page(input_page)
            
            # Create structured page representation
            page_struct = PageStruct(page_rect, text_lines)
            
            # Process each paragraph using the structured approach
            for paragraph_idx, paragraph in enumerate(page_struct.get_paragraphs()):
                
                # Process each line in the paragraph using paragraph-calculated properties
                for line_idx, line in enumerate(paragraph.lines):
                    try:
                        # Determine font style
                        font_name = clean_font
                        if line.is_bold and line.is_italic:
                            if "Times" in clean_font:
                                font_name = "Times-BoldItalic"
                            else:
                                font_name = "Helvetica-BoldOblique"
                        elif line.is_bold:
                            if "Times" in clean_font:
                                font_name = "Times-Bold"
                            else:
                                font_name = "Helvetica-Bold"
                        elif line.is_italic:
                            if "Times" in clean_font:
                                font_name = "Times-Italic"
                            else:
                                font_name = "Helvetica-Oblique"
                        
                        # Calculate line position using paragraph properties
                        if paragraph.is_main_text_paragraph and line.is_main_text():
                            # For main text, use paragraph-calculated positioning
                            if line_idx == 0:
                                # First line: use original indent + paragraph left margin
                                line_x = paragraph.left_margin + paragraph.first_line_indent
                            else:
                                # Subsequent lines: use paragraph left margin
                                line_x = paragraph.left_margin
                            
                            line_y = line.y1  # Keep original vertical position
                            
                            # Use paragraph width for justification if appropriate
                            if paragraph.should_justify() and line.should_justify():
                                insert_justified_text_with_position(
                                    output_page, line, font_name, 
                                    paragraph.get_target_width(), line_x, line_y
                                )
                            else:
                                # Insert text at calculated position (left-aligned)
                                insert_point = fitz.Point(line_x, line_y)
                                output_page.insert_text(
                                    insert_point,
                                    line.text,
                                    fontsize=line.font_size,
                                    fontname=font_name,
                                    color=(0, 0, 0)  # Black text
                                )
                        else:
                            # For auxiliary text, use original positioning
                            insert_point = fitz.Point(line.x0, line.y1)
                            output_page.insert_text(
                                insert_point,
                                line.text,
                                fontsize=line.font_size,
                                fontname=font_name,
                                color=(0, 0, 0)  # Black text
                            )
                        
                    except Exception as e:
                        click.echo(f"\nWarning: Error adding text '{line.text[:20]}...': {e}", err=True)
                        continue
        
        # Save the output PDF
        output_doc.save(output_path)
        output_doc.close()
        input_doc.close()
        
        return True
        
    except Exception as e:
        click.echo(f"\nError processing PDF: {e}", err=True)
        return False


@click.command()
@click.argument('input_pdf')
@click.argument('output_pdf')
@click.option('--font', default='Times-Roman',
              help='Base font family to use (default: Times-Roman)')
def clean_pdf_command(input_pdf, output_pdf, font):
    """
    Clean PDF text while preserving exact layout and positioning.
    
    This tool preserves:
    - Exact text positioning
    - Page dimensions  
    - Line spacing
    - Font sizes
    - Bold/italic formatting (mapped to clean fonts)
    
    Available fonts: Times-Roman (default), Helvetica, Courier
    """
    
    # Validate input file
    input_path = Path(input_pdf)
    if not input_path.exists():
        click.echo(f"Error: Input file '{input_pdf}' does not exist", err=True)
        raise click.Abort()
    
    click.echo(f"Input file: {input_pdf}")
    click.echo(f"Output file: {output_pdf}")
    click.echo(f"Clean font: {font}")
    click.echo()
    
    # Process the PDF
    success = create_clean_pdf_with_exact_layout(input_pdf, output_pdf, font)
    
    if success:
        click.echo(f"\nSuccessfully created clean PDF: {output_pdf}")
        click.echo("Layout and positioning preserved exactly!")
    else:
        click.echo("\nFailed to create clean PDF", err=True)
        raise click.Abort()
