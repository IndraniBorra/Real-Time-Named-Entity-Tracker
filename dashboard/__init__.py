"""
Dashboard Package - Real-time visualization of news analytics

Provides a Flask web application that displays trending keywords
from the Kafka word-stats topic.
"""

from dashboard.app import create_app

__all__ = ['create_app']
