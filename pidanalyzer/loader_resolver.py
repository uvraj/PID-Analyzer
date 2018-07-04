from typing import Iterator, Type

from . import loaders
from .errors import LoaderNotFoundError
from .loaders import Loader


def _find_loaders() -> Iterator[Type[Loader]]:
    """ly
    :return: an iterator of the available Loader classes
    """
    cache_prop = "__cache"
    if hasattr(_find_loaders, cache_prop):
        for loader in getattr(_find_loaders, cache_prop):
            yield loader
    cache = []
    for key, value in loaders.__dict__.items():
        if value.__class__ is not Loader and isinstance(value, Loader.__class__):
            cache.append(value)
            yield value
    setattr(_find_loaders, cache_prop, cache)


def resolve_loader(path: str, tmp_subdir: str) -> Loader:
    """Tries to find the appropriate Loader class for a file.

    :param path: path to the file to inspect
    :param tmp_subdir: name of temp directory
    :return: the resolved Loader
    :raise LoaderNotFoundError: raised when an appropriate Loader wasn't found
    """
    for loader in _find_loaders():
        if loader.is_applicable(path):
            return loader(path, tmp_subdir)
    raise LoaderNotFoundError(path)
