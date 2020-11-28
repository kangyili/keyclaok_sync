from abc import ABC, abstractmethod
import pandas as pd
import json
from keycloak_sync.model.log import logging

logger = logging.getLogger(__name__)


class CSVfile(ABC):
    def __init__(self, filepath: str, separator: str = ';', header=0):
        self.filepath = filepath
        self.separator = separator
        self.data = None
        try:
            self.header = int(header)
        except ValueError:
            try:
                self.header = json.loads(header)
            except json.decoder.JSONDecodeError as error:
                logger.error(f'Unable to transform header : {error}')
                raise error

    @abstractmethod
    def readcsv2users(self):
        raise NotImplementedError

    @abstractmethod
    def isformat(self):
        raise NotImplementedError

    @classmethod
    def readdata(cls, func):
        def wrapper(self):
            try:
                data = pd.read_csv(filepath_or_buffer=self.filepath,
                                   sep=self.separator, header=self.header, skip_blank_lines=True)
                self.data = data
            except FileNotFoundError as error:
                logger.error(f'Unable to find file: {error}')
                raise error
            return func(self)
        return wrapper
