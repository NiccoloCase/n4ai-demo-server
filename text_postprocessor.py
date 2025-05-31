
import re
import logging
from typing import Dict

class TextPostProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text: return ""

        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)

        # Fix common OCR errors
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  # Add space between camelCase
        text = re.sub(r'([0-9])([A-Za-z])', r'\1 \2', text)  # Space between numbers and letters
        text = re.sub(r'([A-Za-z])([0-9])', r'\1 \2', text)  # Space between letters and numbers

        # Clean up bullet points and formatting
        text = re.sub(r'[>•▪▫◦‣⁃]\s*', '• ', text)  # Normalize bullet points
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)  # Convert dashes to bullets

        # Remove page numbers and headers/footers
        text = re.sub(r'\b(?:page|pg\.?)\s*\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)

        # Clean up trademark symbols
        text = re.sub(r'[™®©]', '', text)

        # Remove url links
        text = re.sub(r'https?://\S+', '', text)

        # Remove any remaining excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()



    def process_extracted_text(self, text: str, metadata: Dict) -> Dict:

        cleaned_text = self._clean_text(text)

