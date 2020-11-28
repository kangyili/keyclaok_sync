"""Abstract user class"""
from abc import ABC, abstractmethod


class User(ABC):
    """Define user

    Args:
        ABC : abstract class
    """

    def __init__(self, email, username, firstname, lastname, role, attributes, password=None):
        self.__createdtime = None
        self.__deactivetime = None
        self.__email = email
        self.__username = username
        self.__firstname = firstname
        self.__lastname = lastname
        self.__role = role
        self.__attributes = attributes
        self.__password = password

    @property
    def createdtime(self):
        return self.__createdtime

    @createdtime.setter
    def createdtime(self, createdtime):
        self.__createdtime = createdtime

    @property
    def deactivetime(self):
        return self.__deactivetime

    @deactivetime.setter
    def deactivetime(self, deactivetime):
        self.__deactivetime = deactivetime

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, email):
        self.__email = email

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, username):
        self.__username = username

    @property
    def firstname(self):
        return self.__firstname

    @firstname.setter
    def firstname(self, firstname):
        self.__firstname = firstname

    @property
    def lastname(self):
        return self.__lastname

    @lastname.setter
    def lastname(self, lastname):
        self.__lastname = lastname

    @property
    def role(self):
        return self.__role

    @role.setter
    def role(self, role):
        self.__role = role

    @property
    def attributes(self):
        return self.__attributes

    @attributes.setter
    def attributes(self, attributes):
        self.__attributes = attributes

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, password):
        self.__password = password
    # @abstractmethod
    # def update_user(self):
    #     """Update user's infomation
    #     Raises:
    #         NotImplementedError: Not Implemented Error
    #     """
    #     raise NotImplementedError
