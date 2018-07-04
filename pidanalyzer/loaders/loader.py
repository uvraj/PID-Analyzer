import os
from abc import ABCMeta, abstractmethod
from typing import Iterator, Tuple, Type

from .. import loaders
from ..errors import LoaderNotFoundError


class Loader(metaclass=ABCMeta):
    """Base class for data source loaders.
    """

    def __init__(self, path: str, tmp_subdir: str = "tmp"):
        """
        :param path: path to log data file
        :param tmp_subdir: name of the subdirectory created for temporary files
        """
        self._path = path
        self._tmp_path = os.path.join(os.path.dirname(path), tmp_subdir)
        self._headers = self._read_headers(path)
        self._data = self._read_data(path)

    @staticmethod
    @abstractmethod
    def is_applicable(path: str) -> bool:
        """
        :param path: path to a file to inspect
        :return: True if this Loader is applicable for the file at path
        """
        pass

    @abstractmethod
    def _read_headers(self, path: str) -> Tuple[dict]:
        """
        :return: header fields from data source
        """
        pass

    @abstractmethod
    def _read_data(self, path: str) -> Tuple[dict]:
        """
        :return: frames from data source
        """
        pass

    def clean_up(self):
        """Can be overriden by child classes to clean up temporary files.
        """
        pass

    @property
    def path(self) -> str:
        return str(self._path)

    @property
    def tmp_path(self) -> str:
        return str(self._tmp_path)

    @property
    def headers(self) -> Tuple[dict]:
        return tuple(self._headers)

    @property
    def data(self) -> Tuple[dict]:
        return tuple(self._data)


def _find_loaders() -> Iterator[Type[Loader]]:
    """ly
    :return: an iterator of the available Loader classes
    """
    for key, value in loaders.__dict__.items():
        if value.__class__ is not Loader and isinstance(value, Loader.__class__):
            yield value


def resolve(path: str, tmp_subdir: str) -> Loader:
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
