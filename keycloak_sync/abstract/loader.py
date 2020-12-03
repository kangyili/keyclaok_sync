from abc import ABC, abstractmethod


class Loader(ABC):
    def __init__(self, format):
        self.format = format
