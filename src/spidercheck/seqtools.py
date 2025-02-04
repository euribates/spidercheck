#!/usr/bin/env python

import itertools

"""
Utilidades para trabajar con secuencias.

"""

def first(iterable, condition=lambda x: True, default=None):
    """
    Find and return the first item in the `iterable` that
    satisfies the `condition`.

    Notes:

      - If the condition is not given, returns the first item of
        the iterable. If the iterable is empty, returns the `default`
        value.

    Examples:

        >>> assert first(range(10)) == 0
        >>> assert first(range(10), lambda x: x>3) == 4
        >>> assert first(range(10), lambda x: x>30, default=-1) == -1

    Args:

      iterable (iterable): any iterable

      condition (callale): a callable that acceps a item of the
        sequence and returns a boolean

      defaut (Any): default sentinel value to be used in no
        item in the iterable satisfies the condition. Value
        by default is `None`.


    Returns:

        First item on the sequence to satisty the condition, or
        the sentinel value if no one of the items satisfy the
        condition.
    """
    for item in iterable:
        if condition(item):
            return item
    return default


def count_if(iterable, condition):
    """
    Returns the number of elements in iterable where condition is true.

    The `condition` parameter must be a callable expecting an item
    of the sequence, and returning a boolean.

    Example of use:

        >>> from .seqtools import count_if
        >>> assert count_if([1, 2, 3, 4], lambda item: item % 2 == 0) == 2
    """
    return sum(1 for item in iterable if condition(item))


def split_iter(iterable, condition):
    """
    Split an iterable in two, based on callable condition.

    condition must be a callable that accepts an element
    of the sequence, and returns a boolean. The `split_iter`
    function returns two iterables: First one is for the items
    that are avaluated by `condition` as `True`, second one is
    an iterable for the rest.

    Example:

        >>> pares, impares = split_iter(range(10), lambda x: x % 2 == 0)
        >>> assert list(pares) == [0, 2, 4, 6, 8]
        >>> assert list(impares) == [1, 3, 5, 7, 9]
        >>> lt4, gte4 = split_iter(range(10), lambda x: x < 4)
        >>> assert list(lt4) == [0, 1, 2, 3]
        >>> assert list(gte4) == [4, 5, 6, 7, 8, 9]
    """
    a, b = itertools.tee(iterable, 2)
    positive_iter = (_ for _ in a if condition(_))
    negative_iter = (_ for _ in b if not condition(_))
    return positive_iter, negative_iter


def split_list(iterable, condition):
    '''Like split_iter, but it returns lists instead of iterables.
    '''
    positive_items, negative_items = split_iter(iterable, condition)
    return list(positive_items), list(negative_items)


def batch(iterable, size=2):
    """Take an iterable and split it in several list
    of size _size_, except for the last one, which
    could have less elements.

    Example:

    >>> assert list(batch(range(1, 8), 3)) == [(1, 2, 3), (4, 5, 6), (7,)]
    """
    iterable = iter(iterable)
    while True:
        chunk = []
        for i in range(size):
            try:
                chunk.append(next(iterable))
            except StopIteration:
                if chunk:
                    yield tuple(chunk)
                return
        if chunk:
            yield tuple(chunk)


def text_as_fragments(text, mean_block_size=3000, max_block_size=4000):
    """Devuelve un texto en fragmentos de tamaños similares.

    Intenta dividir las fragmentos en los saltos de línea, o en los espacios.

    Los parámetros por defecto determinan unos fragmentos de tamaño entre
    3000 y 4000 caracteres.
    """
    while text:
        size = len(text)
        if size <= max_block_size:
            yield text
            break
        idx = text.find('\n', mean_block_size)
        if idx == -1 or idx > max_block_size:
            idx = text.find(' ', mean_block_size)
        if idx == -1 or idx > max_block_size:
            idx = max_block_size
        yield text[0:idx]
        text = text[idx:]

