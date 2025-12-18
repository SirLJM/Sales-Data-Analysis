from __future__ import annotations


class StockMonitorError(Exception):
    pass


class DataLoadError(StockMonitorError):
    pass


class ConfigurationError(StockMonitorError):
    pass


class OrderError(StockMonitorError):
    pass


class ValidationError(StockMonitorError):
    pass
