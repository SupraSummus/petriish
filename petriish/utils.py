def without_key(d, key):
    return {
        k: v for k, v in d.items()
        if k != key
    }
