"""Abstract user class"""
from abc import ABC, abstractmethod


class User(ABC):
    """Define user

    Args:
        ABC : abstract class
    """

    def __init__(self, email=None, username=None, firstname=None, lastname=None, role=None, attributes=None, password=None):
        self._createdtime = None
        self._deactivetime = None
        self._email = email
        self._username = username
        self._firstname = firstname
        self._lastname = lastname
        self._role = role
        self._attributes = attributes
        self._password = password

    @property
    def createdtime(self):
        return self._createdtime

    @createdtime.setter
    def createdtime(self, createdtime):
        self._createdtime = createdtime

    @property
    def deactivetime(self):
        return self._deactivetime

    @deactivetime.setter
    def deactivetime(self, deactivetime):
        self._deactivetime = deactivetime

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        self._email = email

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        self._username = username

    @property
    def firstname(self):
        return self._firstname

    @firstname.setter
    def firstname(self, firstname):
        self._firstname = firstname

    @property
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, lastname):
        self._lastname = lastname

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        self._role = role

    @property
    def attributes(self):
        return self._attributes

    @attributes.setter
    def attributes(self, attributes):
        self._attributes = attributes

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = password
