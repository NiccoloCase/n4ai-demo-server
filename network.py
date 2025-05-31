import json
import logging
from pathlib import Path
from typing import Dict, List

from manual_processor import ManualProcessor

NETWORK_DEVICES_SRC = './network_devices.json'
NETWORK_TOPOLOGY_SRC = './network_topology.json'
DOWNLOAD_DIR = './generated/downloads'
EXTRACTED_DIR = './generated/extracted_text'
PROCESSED_DIR = './generated/processed_text'


class Network:
    def __init__(self, devices_src: str = NETWORK_DEVICES_SRC, topology_src: str = NETWORK_TOPOLOGY_SRC):
        self.devices_src = devices_src
        self.topology_src = topology_src
        self.devices = self._load_devices()
        self.topology = self._load_topology()

        self.logger = logging.getLogger(__name__)

        self.logger.info("Network instance created with devices and topology loaded.")

        # Extract manuals data if it does not already exist
        if not self._extract_manuals_data():
            self.logger.error("Failed to extract manuals data. Exiting.")
            raise RuntimeError("Manuals extraction failed")



    def _load_devices(self) -> List[Dict]:
        """Load network devices from the JSON source."""
        try:
            with open(self.devices_src, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load devices from {self.devices_src}: {e}")
            return []

    def _load_topology(self) -> Dict:
        """Load network topology from the JSON source."""
        try:
            with open(self.topology_src, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load topology from {self.topology_src}: {e}")
            return {}

    def _check_extracted_data_exists(self, data_dir: str) -> bool:
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
        if self._check_extracted_data_exists(EXTRACTED_DIR):
            self.logger.info(f"Extracted data found in '{EXTRACTED_DIR}' directory")
            return True

        self.logger.info("No extracted data found. Starting download and extraction process...")


        # Create the directories if they do not exist
        Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(EXTRACTED_DIR).mkdir(parents=True, exist_ok=True)

        # Initialize processor
        self.logger.info(f"Will process {len(self.devices)} manuals")

        try:
            processor = ManualProcessor(
                download_dir=DOWNLOAD_DIR,
                output_dir=EXTRACTED_DIR
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize processor: {e}")
            return False

        # Process manuals
        try:
            self.logger.info("Starting PDF download and text extraction...")
            results = processor.process_all_manuals(self.devices)

            processor.print_summary(results)
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



