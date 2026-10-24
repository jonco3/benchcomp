# resultkey
#
# Key type for benchmark results.

class ResultKey:
    """Identifies a result. Primary results are the benchmark's own scores, as
    opposed to auxiliary measurements such as GC or system usage data.

    Instances are interned so there is only one object for each (name, primary)
    pair. This means the default identity-based equality and hashing give the
    right behaviour for use as dict keys."""

    _instances = {}

    def __new__(cls, name, primary=False):
        key = (name, primary)
        instance = cls._instances.get(key)
        if instance is None:
            instance = object.__new__(cls)
            instance.name = name
            instance.primary = primary
            instance = cls._instances.setdefault(key, instance)
        return instance

    def __reduce__(self):
        return ResultKey, (self.name, self.primary)

    def __repr__(self):
        return f"ResultKey({self.name!r}, primary={self.primary})"
