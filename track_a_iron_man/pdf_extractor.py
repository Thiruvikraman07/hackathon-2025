"""
Simple PDF Extraction Script
Extracts text with inline links from PDF files
"""

import re
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("PyPDF2 not installed. Install with: pip install PyPDF2")
    raise

def extract_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF with inline links

    Args:
        pdf_path: Path to PDF file

    Returns:
        String with text and {links} embedded inline
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Open and read PDF
    with open(pdf_file, 'rb') as file:
        reader = PdfReader(file)

        # Extract all text
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        # Combine all text
        full_text = "\n".join(text_parts)

        # Find URLs in text and format them with {}
        url_pattern = re.compile(r'(https?://[^\s]+)')
        formatted_text = url_pattern.sub(r'{\1}', full_text)

        return formatted_text


if __name__ == "__main__":

    pdf_path = "/Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/cv_lt (2).pdf"
    result = extract_pdf(pdf_path)
    print(result)
