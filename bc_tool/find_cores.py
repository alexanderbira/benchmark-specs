def find_cores(items, prop):
    """
    items: iterable of elements (duplicates allowed)
    prop: function taking a collection (list) of elements and returning True/False.
    Returns: list of minimal subsets (each as a list of items).
    """
    items = list(items)
    n = len(items)
    if n == 0:
        return []

    full = frozenset(range(n))
    prop_cache = {}

    def prop_idx(idx_set):
        key = tuple(sorted(idx_set))
        if key in prop_cache:
            return prop_cache[key]
        subset = [items[i] for i in key]
        prop_cache[key] = bool(prop(subset))
        return prop_cache[key]

    if not prop_idx(full):          # if the full set doesn't satisfy prop, no cores
        return []

    seen = set()
    cores = set()

    def shrink(idx_set):
        key = tuple(sorted(idx_set))
        if key in seen:
            return
        seen.add(key)

        removed_any = False
        for i in list(idx_set):
            new = idx_set - {i}
            if prop_idx(new):
                removed_any = True
                shrink(new)
        if not removed_any:          # cannot remove any single element -> minimal
            cores.add(key)

    shrink(set(full))
    return [[items[i] for i in core] for core in sorted(cores)]