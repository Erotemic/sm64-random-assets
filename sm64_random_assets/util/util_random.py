

def ensure_rng(seed):
    """
    Helper for kwarray < 0.7.1 which doesnt take strings
    """
    import kwarray
    if isinstance(seed, str):
        import hashlib
        raw_bytes = seed.encode('utf-8')
        hasher = hashlib.md5()  # this does not need to be cryptographically secure, use md5 for speed.
        hasher.update(raw_bytes)
        seed = int(hasher.hexdigest(), 16)
    return kwarray.ensure_rng(seed)
