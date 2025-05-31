import json
import logging
import sys
from typing import List, Dict
from api import API
from network import Network


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # This sends to stdout instead of stderr
)

def main():
    logger = logging.getLogger(__name__)

    # Create a new network instance and extract manuals data
    network = Network()



    app = API(network)

    app.start_server(
        host="localhost",
        port=8000,
    )



def load_network_devices(json_file: str) -> List[Dict]:
    """Load hardware network devices data from JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            manuals_data = json.load(f)
        return manuals_data
    except FileNotFoundError:
        print(f"Error: {json_file} not found. Please ensure the file exists.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {json_file}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()