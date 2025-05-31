import logging
from typing import List

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from network import Network
from router import Router



class DeviceConstraints(BaseModel):
    device_ids: List[str]


class API:
    def __init__(self, network: Network):
        self.logger = logging.getLogger(__name__)
        self.network = network
        self.app = FastAPI()
        self._setup_routes()
        self.router = Router()

    def _setup_routes(self):
        self.logger.info("Setting up API routes...")

        @self.app.get("/")
        def get_api_info():
            """Get API information."""
            self.logger.debug("API info endpoint accessed")
            return {
                "name": "N4AI TEST",
                "version": "1.0.0"
            }

        @self.app.get("/devices")
        def get_network_devices():
            return self.network.get_devices()

        @self.app.get("/network_topology")
        def get_network():
            return self.network.topology

        @self.app.post("/route")
        def get_network(constraint_devices: DeviceConstraints = None):
            paths = self.router.route_request(constraint_devices.device_ids if constraint_devices else [], network=self.network)
            return {
                "paths": paths,
                "constraints": constraint_devices,
                "network_topology": self.network.topology
            }

        self.logger.info("API routes setup completed")

    def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the API server."""
        self.logger.info(f"Starting API server on http://{host}:{port}")

        try:
            uvicorn.run(self.app, host=host, port=port, log_level="info")
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise