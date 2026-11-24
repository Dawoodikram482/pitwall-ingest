"""FastAPI application factory."""

from fastapi import FastAPI

from pitwall_ingest import __version__
from pitwall_ingest.adapters.clock import SystemClock
from pitwall_ingest.domain.health import HealthStatus
from pitwall_ingest.services.health import HealthService


def create_app(health_service: HealthService | None = None) -> FastAPI:
    """Build the FastAPI app.

    Args:
        health_service: Service behind ``GET /health``. Tests pass one with a fake clock;
            by default it uses the system clock and the package version.
    """
    service = health_service or HealthService(SystemClock(), __version__)
    app = FastAPI(title="pitwall-ingest", version=__version__)

    @app.get("/health", tags=["ops"])
    def health() -> HealthStatus:
        """Report that the service is up, with its version and uptime."""
        return service.check()

    return app
