import itertools

def check_iterator(iterator):
    iterator1, iterator2 = itertools.tee(iterator, 2)
    try:
        next(iterator1)  # Try to get the first element
        return True, iterator2  # Return True and the untouched iterator
    except StopIteration:
        return False, iter([])  # Return False and an empty iterator if no elements