import json
import logging
from typing import Dict, List

from manual_processor import ManualProcessor

NETWORK_DEVICES_SRC = './network_devices.json'
NETWORK_TOPOLOGY_SRC = './network_topology.json'


class Network:
    def __init__(self, devices_src: str = NETWORK_DEVICES_SRC, topology_src: str = NETWORK_TOPOLOGY_SRC):
        # Initialize logger FIRST
        self.logger = logging.getLogger(__name__)

        self.devices_src = devices_src
        self.topology_src = topology_src
        self.devices = self._load_devices()
        self.topology = self._load_topology()

        self.logger.info("Network instance created with devices and topology loaded.")

        # Initialize the manual processor and load manuals
        self.manual_processor = ManualProcessor(self.devices)

    def _load_devices(self) -> List[Dict]:
        """Load network devices from the JSON source."""
        try:
            with open(self.devices_src, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    self.logger.warning(f"Devices file {self.devices_src} is empty")
                    return []
                return json.loads(content)
        except FileNotFoundError:
            self.logger.error(f"Devices file not found: {self.devices_src}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in devices file {self.devices_src}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to load devices from {self.devices_src}: {e}")
            return []

    def _load_topology(self) -> Dict:
        """Load network topology from the JSON source."""
        try:
            with open(self.topology_src, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    self.logger.warning(f"Topology file {self.topology_src} is empty")
                    return {"topology": {"nodes": [], "connections": []}}
                return json.loads(content)
        except FileNotFoundError:
            self.logger.error(f"Topology file not found: {self.topology_src}")
            return {"topology": {"nodes": [], "connections": []}}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in topology file {self.topology_src}: {e}")
            return {"topology": {"nodes": [], "connections": []}}
        except Exception as e:
            self.logger.error(f"Failed to load topology from {self.topology_src}: {e}")
            return {"topology": {"nodes": [], "connections": []}}


    def get_devices(self) -> List[Dict]:
        """Get the list of network devices that are actually used in the topology (no duplicates)."""
        self.logger.debug("Fetching network devices")

        # Extract unique device_ids from topology nodes
        used_device_ids = set()
        if self.topology and 'topology' in self.topology:
            for node in self.topology['topology'].get('nodes', []):
                if 'device_id' in node:
                    used_device_ids.add(node['device_id'])

        # Filter devices to only include those used in topology
        filtered_devices = []
        for device in self.devices:
            if device.get('_id') in used_device_ids:
                filtered_devices.append(device)

        # Populate manuals for each filtered device
        for device in filtered_devices:
            device['manual_text'] = self.manual_processor.get_manual(device)

        return filtered_devices