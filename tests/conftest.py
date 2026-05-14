def pytest_configure(config):
    config.addinivalue_line("markers", "unit: pure unit tests, no I/O")
    config.addinivalue_line("markers", "integration: requires database or external services")
    config.addinivalue_line("markers", "smoke: critical path, run first")
