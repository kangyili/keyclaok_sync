import logging
from datetime import datetime
from typing import Union

import cerberus
import coloredlogs
import pandas as pd
from keycloak import KeycloakAdmin, exceptions
from keycloak_sync.model.csvloader import CSVLoader
from keycloak_sync.model.kcuser import KCUser

logger = logging.getLogger(__name__)


class KeycloakError(Exception):
    """Exception raised for errors in the Keycloak.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


def connect(func):
    """a wrapper for connecting"""

    def wrapper(self, *args, **kwargs):
        try:
            self.kc_admin = KeycloakAdmin(server_url=self.server_url,
                                          client_id=self.client_id,
                                          realm_name=self.realm_name,
                                          client_secret_key=self.client_secret_key,
                                          verify=True)
        except (exceptions.KeycloakConnectionError, exceptions.KeycloakGetError):
            raise KeycloakError(f'Unable to connect server')
        return func(self, *args, **kwargs)
    return wrapper


class Keycloak:
    def __init__(self, server_url: str, client_id: str, realm_name: str, client_secret_key: str):
        self.kc_admin = None
        self.server_url = server_url
        self.client_id = client_id
        self.realm_name = realm_name
        self.client_secret_key = client_secret_key

    @staticmethod
    def set_log_level(level: str):
        """set keycloak log level

        Args:
            level (str): log level
        """
        coloredlogs.install(level=level, logger=logger)

    def _assign_role_to_user(self, user: KCUser):
        """assgin user's role with its parameter

        Args:
            user (KCUser): user to assign

        Raises:
            KeycloakError: unable to assign role
        """
        try:
            user_id = self.kc_admin.get_user_id(username=user.username)
            role_id = self.kc_admin.get_realm_role(user.role)['id']
        except exceptions.KeycloakGetError:
            raise KeycloakError(f'Unable to find role: {user.role}')
        roles_info = [{
            'id': role_id,
            'name': user.role
        }]
        try:
            self.kc_admin.assign_realm_roles(user_id=user_id,
                                             client_id=self.kc_admin.client_id,
                                             roles=roles_info)
        except exceptions.KeycloakGetError:
            raise KeycloakError(
                f'Unable to assign user {user.username} with role {user.role}')

    @connect
    def add_user(self, user: KCUser):
        """Add user to keycloak

        Args:
            user (KCser): A keycloak user instance

        Raises:
            error: exceptions.KeycloakGetError
        """
        user_id = self.kc_admin.get_user_id(username=user.username)
        if user_id:
            self.kc_admin.delete_user(user_id=user_id)
            logger.warning(f'update existed user: {user.username}')
        payload = {"email": user.email,
                   "username": user.username,
                   "enabled": True,
                   "emailVerified": True,
                   "firstName": user.firstname,
                   "lastName": user.lastname,
                   "attributes": user.attributes
                   }
        if not pd.isnull(user.password):
            payload['credentials'] = [
                {"value": user.password, "type": "password", }]

        try:
            self.kc_admin.create_user(payload)
            logger.info(f'Add user: {user.username} successfully')
        except exceptions.KeycloakGetError as error:
            raise KeycloakError(
                f'Unable to create user {user.username}: {error}')
        self._assign_role_to_user(user)

    def add_users(self, users: list):
        """Add list of users to keycloak

        Args:
            users (list): A list of BM user instances
        """
        list(map(self.add_user, users))

    def delete_user(self, username: str):
        """Delete a user from keycloak

        Args:
            username (str): user index

        Returns:
            bool: Success is True, otherwise is False
        """
        try:
            user_id = self.kc_admin.get_user_id(username=username)
            self.kc_admin.delete_user(user_id=user_id)
            logger.info(f'Delete user: {username}')
        except exceptions.KeycloakGetError:
            raise KeycloakError(f'User: {username} does not exist')

    @connect
    def delete_all_users(self):
        """Delete all users from keycloak
        """
        list(map(lambda x: self.delete_user(
            username=x['username']), self.kc_admin.get_users()))

    def get_user_realm_role(self, csvloader: CSVLoader, user_id: str) -> Union[str, None]:
        for role in csvloader.values["export_rules"]["available_roles"]:
            try:
                for user in self.kc_admin.get_realm_role_members(role):
                    if user['id'] == user_id:
                        return role
            except exceptions.KeycloakGetError as error:
                raise KeycloakError(f'Role: {role} does not exist in realm')
        return None

    @staticmethod
    def fliter_user(csvloader: CSVLoader, user: dict, rule: str) -> bool:
        """fliter users

        Args:
            csvloader (CSVLoader): a Csvloder instance to provide values file
            user (dict): user's parameter name and vlaue
            rule (str): schema used by cerberus

        Raises:
            KeycloakError: unknwon rule

        Returns:
            bool: return true when user is satisfied by rule
        """
        try:
            validator = cerberus.Validator(
                csvloader.load_identifier(rule))
            name = csvloader.values[rule]['identifier']['name']
            return validator.validate({name: user[name]})
        except cerberus.schema.SchemaError as error:
            raise KeycloakError(f'Unknown rule: {error}')

    def get_user(self, csvloader: CSVLoader, user_id: str, rule: str) -> Union[KCUser, None]:
        """get user after flitering

        Args:
            csvloader (CSVLoader): a Csvloder instance to provide values file
            user_id (str): user id on keycloak
            rule (str): schema used by cerberus

        Raises:
            KeycloakError: invalide user id

        Returns:
            Union[KCUser, None]: if user exist then return user otherwise return none
        """
        try:
            user = self.kc_admin.get_user(user_id=user_id)
        except exceptions.KeycloakGetError as error:
            raise KeycloakError(f'Unable to find user id: f{user_id}: {error}')
        if Keycloak.fliter_user(csvloader=csvloader, user=user, rule=rule):
            role = self.get_user_realm_role(
                csvloader=csvloader, user_id=user_id)
            attributes = dict(
                map(lambda item: (item[0], ''.join(item[1])), user['attributes'].items()))
            kcuser = KCUser(email=user['email'], username=user['username'],
                            firstname=user['firstName'], lastname=user['lastName'],
                            role=role, attributes=attributes)
            kcuser.createdtime = datetime.fromtimestamp(
                int(str(user['createdTimestamp'])[:10])).strftime('%d/%m/%y')
            return kcuser
        else:
            return None

    @connect
    def get_users(self, csvloader: CSVLoader, rule: str) -> list:
        """get list of users after flitering bt rules

        Args:
            csvloader (CSVLoader): a Csvloder instance to provide values file
            rule (str): schema used by cerberus

        Returns:
            list: list of users
        """
        logger.info(
            f"Use schema: {csvloader.load_identifier(rule)}")
        list_users = []
        for user in self.kc_admin.get_users():
            user_ = self.get_user(csvloader=csvloader,
                                  user_id=user['id'], rule=rule)
            if user_:
                logger.info(f'Get user {user_.username}')
                list_users.append(user_)
        return list_users

    @connect
    def delete_users(self, list_users: list):
        """delete users by giving list of users

        Args:
            list_users (list): list of users to be deleted
        """
        list(map(lambda x: self.delete_user(
            username=x.username), list_users))
