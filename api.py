import json
import os
import logging
from pathlib import Path
from typing import List, Dict
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

class API:
    def __init__(self, extracted_text_dir: str, results_file_pattern: str):
        self.logger = logging.getLogger(__name__)

        self.extracted_text_dir = Path(extracted_text_dir)
        self.results_file_pattern = results_file_pattern
        self.app = FastAPI(title="N4AI TEST", version="1.0.0")

        self.logger.info(f"Initializing API with text directory: {self.extracted_text_dir}")
        self.logger.info(f"Results file pattern: {self.results_file_pattern}")

        self._setup_routes()

    def load_extraction_results(self) -> List[Dict]:
        """Load extraction results from the latest results file."""
        self.logger.debug("Loading extraction results...")

        results_files = list(Path(".").glob(f"{self.results_file_pattern}*.json"))
        if not results_files:
            self.logger.warning(f"No results files found matching pattern: {self.results_file_pattern}*.json")
            return []

        latest_file = max(results_files, key=os.path.getctime)
        self.logger.info(f"Loading results from: {latest_file}")

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                self.logger.info(f"Successfully loaded {len(results)} extraction results")
                return results
        except Exception as e:
            self.logger.error(f"Error loading results from {latest_file}: {e}")
            return []

    def load_text_content(self, file_path: str) -> str:
        """Load text content from a file."""
        self.logger.debug(f"Loading text content from: {file_path}")

        try:
            full_path = self.extracted_text_dir / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.logger.debug(f"Successfully loaded {len(content)} characters from {file_path}")
                return content
        except Exception as e:
            self.logger.error(f"Error loading text from {file_path}: {e}")
            return ""

    def _setup_routes(self):
        self.logger.info("Setting up API routes...")

        @self.app.get("/")
        def get_api_info():
            """Get API information."""
            self.logger.debug("API info endpoint accessed")
            return {
                "name": "N4AI TEST",
                "version": "1.0.0",
                "extracted_text_dir": str(self.extracted_text_dir),
                "results_pattern": self.results_file_pattern
            }

        @self.app.get("/manuals")
        def get_manuals():
            """Get list of all available manuals."""
            self.logger.info("Manuals list endpoint accessed")
            results = self.load_extraction_results()
            return {
                "count": len(results),
                "manuals": results
            }

        @self.app.get("/manual/{manual_id}")
        def get_manual(manual_id: str):
            """Get a specific manual by ID."""
            self.logger.info(f"Manual endpoint accessed for ID: {manual_id}")
            results = self.load_extraction_results()
            manual = next((m for m in results if str(m.get('id')) == manual_id), None)
            if not manual:
                self.logger.warning(f"Manual not found for ID: {manual_id}")
                raise HTTPException(status_code=404, detail="Manual not found")

            self.logger.debug(f"Manual found for ID: {manual_id}")
            return manual

        @self.app.get("/search")
        def search_manuals(q: str = Query(..., description="Search query")):
            """Search through manuals."""
            self.logger.info(f"Search endpoint accessed with query: '{q}'")
            results = self.load_extraction_results()
            filtered_results = []

            for manual in results:
                # Search in title, content, or other fields
                searchable_text = f"{manual.get('title', '')} {manual.get('content', '')}".lower()
                if q.lower() in searchable_text:
                    filtered_results.append(manual)

            self.logger.info(f"Search returned {len(filtered_results)} results for query: '{q}'")
            return {
                "query": q,
                "count": len(filtered_results),
                "results": filtered_results
            }

        @self.app.get("/stats")
        def get_stats():
            """Get statistics about the document collection."""
            self.logger.info("Stats endpoint accessed")
            results = self.load_extraction_results()
            text_files = list(self.extracted_text_dir.glob("*.txt")) if self.extracted_text_dir.exists() else []

            stats = {
                "total_manuals": len(results),
                "total_text_files": len(text_files),
                "extraction_results_pattern": self.results_file_pattern,
                "text_directory": str(self.extracted_text_dir)
            }

            self.logger.debug(f"Stats generated: {stats}")
            return stats

        @self.app.get("/download/{file_id}")
        def download_text_file(file_id: str):
            """Download a text file by ID."""
            self.logger.info(f"Download endpoint accessed for file ID: {file_id}")

            # Assuming file_id corresponds to a filename
            file_path = self.extracted_text_dir / f"{file_id}.txt"

            if not file_path.exists():
                self.logger.warning(f"File not found for download: {file_path}")
                raise HTTPException(status_code=404, detail="File not found")

            self.logger.info(f"Serving file for download: {file_path}")
            return FileResponse(
                path=file_path,
                filename=f"{file_id}.txt",
                media_type='text/plain'
            )

        @self.app.get("/devices")
        def get_network_devices():
            """Get network devices (placeholder endpoint)."""
            self.logger.info("Network devices endpoint accessed")
            self.logger.warning("Network devices endpoint not yet implemented")
            return {"message": "Network devices endpoint - implementation needed"}

        self.logger.info("API routes setup completed")

    def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the API server."""
        self.logger.info(f"Starting API server on http://{host}:{port}")
        self.logger.info(f"Extracted text directory: {self.extracted_text_dir}")
        self.logger.info(f"Results file pattern: {self.results_file_pattern}")

        self.logger.info("Available endpoints:")
        endpoints = [
            " GET / - API info",
            " GET /manuals - List all manuals",
            " GET /manual/{id} - Get specific manual",
            " GET /search?q= - Search manuals",
            " GET /stats - Get statistics",
            " GET /download/{id} - Download text file",
            " GET /devices - Get network devices"
        ]

        for endpoint in endpoints:
            self.logger.info(endpoint)

        try:
            uvicorn.run(self.app, host=host, port=port, log_level="info")
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise