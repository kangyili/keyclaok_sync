from abc import ABC, abstractmethod
from pathlib import Path, PurePath


class StorageProvider(ABC):
    """basic storage provider"""
    class StorageProviderERROR(Exception):
        """Exception raised for errors in the StorageProvider.

        Attributes:
            message -- explanation of the error
        """

        def __init__(self, message):
            self.message = message

    def __init__(self, type: str):
        self._type = type

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @abstractmethod
    def download(bucket_name: str, source_file: PurePath, destination_file: Path):
        raise NotImplementedError
