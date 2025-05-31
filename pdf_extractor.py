import logging
import PyPDF2
import pdfplumber


class PDFExtractor:
    """Handles PDF text extraction using multiple methods."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_with_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction failed: {e}")
            return ""

    def extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
        except Exception as e:
            self.logger.error(f"pdfplumber extraction failed: {e}")
            return ""

    def extract_text(self, pdf_path: str) -> str:
        """Extract text using the best available method."""
        # Try pdfplumber first (generally better)
        text = self.extract_with_pdfplumber(pdf_path)

        # Fallback to PyPDF2 if pdfplumber fails or returns empty
        if not text:
            self.logger.info("Trying PyPDF2 as fallback...")
            text = self.extract_with_pypdf2(pdf_path)

        return text
