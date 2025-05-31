import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
import time
import urllib3
from pdf_extractor import PDFExtractor
from text_postprocessor import TextPostProcessor

DOWNLOAD_DIR = './generated/downloads'
EXTRACTED_DIR = './generated/extracted_text'
OUTPUT_DIR = './generated/processed_text'

class ManualProcessor:
    def __init__(self, devices: List[Dict]):
        self.pdf_extractor = PDFExtractor()

        # Create the directories if they do not exist
        Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(EXTRACTED_DIR).mkdir(parents=True, exist_ok=True)
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        # Disable SSL verification
        self.session.verify = False
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Devices data
        self.devices = devices

        # Download and extract manuals data if it does not already exist
        if not self._extract_manuals_data():
            self.logger.error("Failed to extract manuals data. Exiting.")
            raise RuntimeError("Manuals extraction failed")

        # Post-processing of the extracted text
        if not self._process_extracted_manuals():
            self.logger.error("Failed to process extracted manuals. Exiting.")
            raise RuntimeError("Processing of extracted manuals failed")


    def get_manual(self, device) -> Optional[str]:
        """Get the processed manual data for a device."""
        manual_name = self.get_manual_safe_name(device)
        manual_path = Path(OUTPUT_DIR) / f"{manual_name}.txt"

        # Get the content of the manual if it exists
        if manual_path.exists():
            try:
                with open(manual_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"Failed to read manual {manual_name}: {e}")
                return None
        else:
            self.logger.warning(f"Manual file not found: {manual_path}")
            return None

    def sanitize_filename(self, filename: str) -> str:
        """Clean filename for safe filesystem storage."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:200]  # Limit length




    def download_pdf(self, url: str, filename: str) -> Optional[str]:
        """Download PDF from URL with multiple retry strategies."""
        file_path = Path(DOWNLOAD_DIR) / filename

        # Skip if already downloaded
        if file_path.exists():
            self.logger.info(f"File already exists: {filename}")
            return str(file_path)

        # Try multiple download strategies
        strategies = [
            self._download_standard,
            self._download_with_ssl_context
        ]

        for i, strategy in enumerate(strategies, 1):
            try:
                self.logger.info(f"Downloading (attempt {i}): {url}")
                result = strategy(url, file_path)
                if result:
                    self.logger.info(f"Downloaded successfully: {filename}")
                    return str(file_path)
            except Exception as e:
                self.logger.warning(f"Download attempt {i} failed: {e}")
                if i < len(strategies):
                    self.logger.info(f"Trying alternative method...")
                    time.sleep(2)  # Brief pause between attempts

        self.logger.error(f"All download attempts failed for: {url}")
        return None

    def _download_standard(self, url: str, file_path: Path) -> bool:
        """Standard download method."""
        response = self.session.get(url, timeout=30, stream=True)
        response.raise_for_status()
        return self._save_response_to_file(response, file_path)

    def _download_with_ssl_context(self, url: str, file_path: Path) -> bool:
        """Download with custom SSL context."""
        import ssl
        import urllib.request

        # Create unverified SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Create custom opener
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
        urllib.request.install_opener(opener)

        # Add headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept', 'application/pdf,*/*')

        with urllib.request.urlopen(req, timeout=30) as response:
            with open(file_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        return file_path.exists() and file_path.stat().st_size > 0


    def _save_response_to_file(self, response: requests.Response, file_path: Path) -> bool:
        """Save HTTP response to file with progress tracking."""
        # Check if it's actually a PDF
        content_type = response.headers.get('content-type', '')
        if 'pdf' not in content_type.lower() and 'octet-stream' not in content_type.lower():
            self.logger.warning(f"Content type may not be PDF: {content_type}")

        # Download with progress
        total_size = int(response.headers.get('content-length', 0))
        with open(file_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            print()  # New line

        return file_path.exists() and file_path.stat().st_size > 0


    def get_manual_safe_name(self, manual_data: Dict) -> str:
        """Generate a safe filename for the manual."""
        name = manual_data.get('name', 'Unknown')
        maker = manual_data.get('maker', 'Unknown')

        # Sanitize and create a safe filename
        safe_name = f"{self.sanitize_filename(maker)}_{self.sanitize_filename(name)}"
        return safe_name


    def process_manual(self, manual_data: Dict) -> Dict:
        """Process a single manual entry."""
        name = manual_data.get('name', 'Unknown')
        maker = manual_data.get('maker', 'Unknown')
        url = manual_data.get('manual', '')

        self.logger.info(f"Processing: {name} by {maker}")

        result = {
            'id': manual_data.get('_id', {}),
            'name': name,
            'maker': maker,
            'category': manual_data.get('category', ''),
            'url': url,
            'status': 'pending',
            'text': '',
            'error': None
        }

        if not url:
            result['status'] = 'error'
            result['error'] = 'No manual URL provided'
            return result

        # Create filename
        parsed_url = urlparse(url)
        original_filename = Path(parsed_url.path).name
        if not original_filename.endswith('.pdf'):
            original_filename += '.pdf'


        safe_name = self.get_manual_safe_name(manual_data)

        # Download PDF
        pdf_path = self.download_pdf(url, safe_name)
        if not pdf_path:
            result['status'] = 'error'
            result['error'] = 'Failed to download PDF'
            return result

        # Extract text
        try:
            text = self.pdf_extractor.extract_text(pdf_path)
            if text:
                # Save extracted text
                text_filename = f"{safe_name}.txt"
                text_path = Path(EXTRACTED_DIR) / text_filename

                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                result['status'] = 'success'
                result['text'] = text
                result['text_file'] = str(text_path)
                self.logger.info(f"Successfully extracted text: {len(text)} characters")
            else:
                result['status'] = 'error'
                result['error'] = 'No text could be extracted from PDF'

        except Exception as e:
            result['status'] = 'error'
            result['error'] = f'Text extraction failed: {str(e)}'
            self.logger.error(f"Text extraction failed for {name}: {e}")

        return result

    def process_all_manuals(self, network_devices_data: List[Dict]) -> List[Dict]:
        """Process all manuals in the dataset."""
        results = []
        total = len(network_devices_data)

        self.logger.info(f"Starting processing of {total} manuals...")

        for i, manual in enumerate(network_devices_data, 1):
            self.logger.info(f"\n--- Processing {i}/{total} ---")
            result = self.process_manual(manual)
            results.append(result)

            # Small delay to be respectful to servers
            time.sleep(1)

        return results

    def save_results(self, results: List[Dict], filename: str):
        """Save processing results to JSON file."""
        results_path = Path(EXTRACTED_DIR) / filename
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"Results saved to: {results_path}")

    def print_summary(self, results: List[Dict]):
        """Print processing summary."""
        total = len(results)
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = total - successful

        print(f"\n{'=' * 60}")
        print(f"PROCESSING SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total manuals: {total}")
        print(f"Successfully processed: {successful}")
        print(f"Failed: {failed}")

        if failed > 0:
            print(f"\nFailed manuals:")
            for result in results:
                if result['status'] == 'error':
                    print(f"  - {result['name']}: {result['error']}")



    def _check_data_exists(self, data_dir: str) -> bool:
        """
        Check if extracted manuals data already exists in the output directory.
        """
        output_path = Path(data_dir)
        if not output_path.exists(): return False

        # Check if there are any .txt files in the output directory
        txt_files = list(output_path.glob("*.txt"))
        return len(txt_files) > 0


    def _extract_manuals_data(self) -> bool:

        self.logger.info("Checking if extracted data exists...")

        # Check if extracted data already exists
        if self._check_data_exists(EXTRACTED_DIR):
            self.logger.info(f"Extracted data found in '{EXTRACTED_DIR}' directory")
            return True

        self.logger.info(f"No extracted data found in '{EXTRACTED_DIR}' directory. Starting download and extraction process...")

        # Initialize processor
        self.logger.info(f"Will process {len(self.devices)} manuals")

        try:
            self.logger.info("Starting PDF download and text extraction...")
            results = self.process_all_manuals(self.devices)

            self.print_summary(results)

            successful_results = [r for r in results if r['status'] == 'success']
            if successful_results:
                total_chars = sum(len(r.get('text', '')) for r in successful_results)
                avg_chars = total_chars // len(successful_results) if successful_results else 0
                self.logger.info(f"Text extraction statistics:")
                self.logger.info(f"  Total characters extracted: {total_chars:,}")
                self.logger.info(f"  Average characters per manual: {avg_chars:,}")

            self.logger.info("PDF extraction completed successfully")
            return True

        except KeyboardInterrupt:
            self.logger.info("Processing interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            return False


    def _process_extracted_manuals(self):
        """
        Process the extracted manuals text files.
        This method can be extended to perform additional processing on the extracted text.
        """
        self.logger.info("Processing extracted manuals...")

        # check if extracted data exists
        if not self._check_data_exists(EXTRACTED_DIR):
            self.logger.warning(f"No extracted data found in '{EXTRACTED_DIR}' directory. Skipping processing.")
            return True

        # Check if the data was already processed
        if self._check_data_exists(OUTPUT_DIR):
            self.logger.info(f"Processed data found in '{OUTPUT_DIR}' directory. Skipping processing.")
            return True

        try:

            extracted_files = list(Path(EXTRACTED_DIR).glob("*.txt"))
            self.logger.info(f"Found {len(extracted_files)} extracted text files in '{EXTRACTED_DIR}' directory.")

            text_post_processor = TextPostProcessor()
            text_post_processor.process_multiple_files(extracted_files, OUTPUT_DIR)

            return True

        except Exception as e:
            self.logger.error(f"Error during processing of extracted manuals: {e}")
            return False
