import json
import logging
from pathlib import Path
from typing import Dict, List

from manual_processor import ManualProcessor

NETWORK_DEVICES_SRC = './network_devices.json'
NETWORK_TOPOLOGY_SRC = './network_topology.json'


class Network:
    def __init__(self, devices_src: str = NETWORK_DEVICES_SRC, topology_src: str = NETWORK_TOPOLOGY_SRC):
        self.devices_src = devices_src
        self.topology_src = topology_src
        self.devices = self._load_devices()
        self.topology = self._load_topology()

        self.logger = logging.getLogger(__name__)

        self.logger.info("Network instance created with devices and topology loaded.")

        # Initialize the manual processor and load manuals
        self.manual_processor = ManualProcessor(self.devices)



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



