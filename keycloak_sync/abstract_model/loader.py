from abc import ABC, abstractmethod


class Loader(ABC):
    """ basic loader"""

    def __init__(self, format):
        self.format = format
