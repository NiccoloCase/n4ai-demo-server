import re
import logging

from pathlib import Path
from typing import Dict

class TextPostProcessor:
    def __init__(self, encoding: str = 'utf-8'):
        """
        Initialize TextPostProcessor with configurable encoding.

        Args:
            encoding (str): Text file encoding (default: 'utf-8')
        """
        self.logger = logging.getLogger(__name__)
        self.encoding = encoding

        # Configure logging if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

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


        # Removed repeted sequences of symbols like '===' or '---'
        # es: ================================================================================
        text = re.sub(r'[-=.]{3,}', '', text)


        # Remove any remaining excessive whitespace
        text = re.sub(r'\s+', ' ', text)



        return text.strip()

    def process_text_file(self, source_file: str, target_directory: str,
                          preserve_extension: bool = True) -> bool:
        """
        Process a text file and save the cleaned version to target directory.

        Args:
            source_file (str): Path to the source text file
            target_directory (str): Directory where processed file will be saved
            preserve_extension (bool): Whether to keep original file extension

        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            # Validate source file
            source_path = Path(source_file)
            if not source_path.exists():
                self.logger.error(f"Source file does not exist: {source_file}")
                return False

            if not source_path.is_file():
                self.logger.error(f"Source path is not a file: {source_file}")
                return False

            # Create target directory if it doesn't exist
            target_path = Path(target_directory)
            target_path.mkdir(parents=True, exist_ok=True)

            # Read source file
            self.logger.info(f"Reading source file: {source_file}")
            with open(source_path, 'r', encoding=self.encoding) as file:
                text_content = file.read()

            # Process the text
            self.logger.info("Processing text content...")
            cleaned_text = self._clean_text(text_content)

            # Determine output filename
            if preserve_extension:
                output_filename = source_path.name
            else:
                output_filename = source_path.stem + '.txt'

            output_path = target_path / output_filename

            # Write processed text to target file
            self.logger.info(f"Writing processed text to: {output_path}")
            with open(output_path, 'w', encoding=self.encoding) as file:
                file.write(cleaned_text)

            self.logger.info(f"Successfully processed {source_file} -> {output_path}")
            return True

        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error reading {source_file}: {e}")
            return False
        except PermissionError as e:
            self.logger.error(f"Permission error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error processing {source_file}: {e}")
            return False

    def process_multiple_files(self, source_files: list, target_directory: str) -> Dict[str, bool]:
        """
        Process multiple text files.

        Args:
            source_files (list): List of source file paths
            target_directory (str): Directory where processed files will be saved

        Returns:
            Dict[str, bool]: Dictionary mapping source files to success status
        """
        results = {}

        self.logger.info(f"Processing {len(source_files)} files...")

        for source_file in source_files:
            success = self.process_text_file(source_file, target_directory)
            results[source_file] = success

        successful = sum(results.values())
        self.logger.info(f"Processing complete: {successful}/{len(source_files)} files successful")

        return results

