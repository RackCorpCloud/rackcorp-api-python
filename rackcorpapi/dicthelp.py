def get_first(d: dict, keys: list, default=None):
    for key in keys:
        if key in d:
            return d[key]
    return default
