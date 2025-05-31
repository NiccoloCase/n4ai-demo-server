import logging
import uvicorn
from fastapi import FastAPI

from network import Network

class API:
    def __init__(self, network: Network):
        self.logger = logging.getLogger(__name__)
        self.network = network
        self.app = FastAPI()  # Create FastAPI instance first
        self._setup_routes()  # Then setup routes

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

        self.logger.info("API routes setup completed")

    def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the API server."""
        self.logger.info(f"Starting API server on http://{host}:{port}")

        try:
            uvicorn.run(self.app, host=host, port=port, log_level="info")
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise