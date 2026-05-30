"""Pytest configuration.

Unit tests use unittest.mock to mock the Pub/Sub subscriber and SQLAlchemy
Session — no real broker or database is required to run the tests.
"""
