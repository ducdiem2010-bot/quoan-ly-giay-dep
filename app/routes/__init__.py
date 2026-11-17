"""Route modules grouped by feature. Keep Flask endpoint names unchanged."""
from .public import register_routes

__all__ = ["register_routes"]
