"""
Prometheus Fallback pour tests sans dépendances
"""


class Counter:
    def __init__(self, name, description, labelnames=None, registry=None):
        _ = registry  # Mark as intentionally unused
        self.name = name
        self.description = description
        self.labelnames = labelnames or []
        self._value = 0

    def labels(self, **_kwargs):
        return self

    def inc(self, amount=1):
        self._value += amount


class Histogram:
    def __init__(self, name, description, labelnames=None, registry=None, buckets=None):
        _ = registry  # Mark as intentionally unused
        _ = buckets  # Mark as intentionally unused
        self.name = name
        self.description = description
        self.labelnames = labelnames or []
        self._observations = []

    def labels(self, **_kwargs):
        return self

    def observe(self, amount):
        self._observations.append(amount)


class Gauge:
    def __init__(self, name, description, labelnames=None, registry=None):
        _ = registry  # Mark as intentionally unused
        self.name = name
        self.description = description
        self.labelnames = labelnames or []
        self._value = 0

    def labels(self, **_kwargs):
        return self

    def set(self, value):
        self._value = value

    def inc(self, amount=1):
        self._value += amount

    def dec(self, amount=1):
        self._value -= amount


class CollectorRegistry:
    def __init__(self):
        pass


class Info:
    def __init__(self, name, description, registry=None):
        _ = registry  # Mark as intentionally unused
        self.name = name
        self.description = description

    def info(self, info_dict):
        pass


def start_http_server(port, registry=None):
    _ = registry  # Mark as intentionally unused
    """Mock server start"""
    print(f"Mock Prometheus server started on port {port}")


# Instance par défaut
REGISTRY = CollectorRegistry()
