import logging
from datetime import datetime
from typing import Union

import cerberus
import coloredlogs
import pandas as pd
from keycloak import KeycloakAdmin, exceptions
from keycloak_sync.model.csvloader import CSVLoader, Template
from keycloak_sync.model.kcuser import KCUser

logger = logging.getLogger(__name__)


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
            raise Keycloak.KeycloakError(f'Unable to connect server')
        return func(self, *args, **kwargs)
    return wrapper


class Keycloak:
    class Keycloak_API:
        ID = 'id'
        FIRSTNAME = 'firstName'
        LASTNAME = 'lastName'
        CREATEDTIME = 'createdTimestamp'
        EMAIL = 'email'
        USERNAME = 'username'
        ATTRIBUTES = 'attributes'
        ROLE_NAME = 'name'
        USER_ENABLE = 'enabled'
        EMAIL_VERIFICATION = 'emailVerified'
        CREDENTIALS = 'credentials'
        CREDENTIALS_VALUE = 'value'
        CREDENTIALS_TYPE = 'type'
        CREDENTIALS_TYPE_VALUE = 'password'

    class KeycloakError(Exception):
        """Exception raised for errors in the Keycloak.

        Attributes:
            message -- explanation of the error
        """

        def __init__(self, message):
            self.message = message

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
            user_id = self.kc_admin.get_user_id(username=user.username.lower())
            role_id = self.kc_admin.get_realm_role(
                user.role)[Keycloak.Keycloak_API.ID]
        except exceptions.KeycloakGetError:
            raise Keycloak.KeycloakError(f'Unable to find role: {user.role}')
        roles_info = [{
            Keycloak.Keycloak_API.ID: role_id,
            Keycloak.Keycloak_API.ROLE_NAME: user.role
        }]
        try:
            self.kc_admin.assign_realm_roles(user_id=user_id,
                                             client_id=self.kc_admin.client_id,
                                             roles=roles_info)
        except exceptions.KeycloakGetError:
            raise Keycloak.KeycloakError(
                f'Unable to assign user {user.username} with role {user.role}')

    def _add_user(self, user: KCUser):
        """Add user to keycloak

        Args:
            user (KCser): A keycloak user instance

        Raises:
            error: exceptions.KeycloakGetError
        """
        user_id = self.kc_admin.get_user_id(username=user.username.lower())
        if user_id:
            self.kc_admin.delete_user(user_id=user_id)
            logger.warning(f'update existed user: {user.username}')
        payload = {Keycloak.Keycloak_API.EMAIL: user.email,
                   Keycloak.Keycloak_API.USERNAME: user.username,
                   Keycloak.Keycloak_API.USER_ENABLE: True,
                   Keycloak.Keycloak_API.EMAIL_VERIFICATION: True,
                   Keycloak.Keycloak_API.FIRSTNAME: user.firstname,
                   Keycloak.Keycloak_API.LASTNAME: user.lastname,
                   Keycloak.Keycloak_API.ATTRIBUTES: user.attributes
                   }
        if not pd.isnull(user.password):
            payload[Keycloak.Keycloak_API.CREDENTIALS] = [
                {Keycloak.Keycloak_API.CREDENTIALS_VALUE: user.password, Keycloak.Keycloak_API.CREDENTIALS_TYPE: Keycloak.Keycloak_API.CREDENTIALS_TYPE_VALUE}]

        try:
            self.kc_admin.create_user(payload)
            logger.info(f'Add user: {user.username} successfully')
        except exceptions.KeycloakGetError as error:
            raise Keycloak.KeycloakError(
                f'Unable to create user {user.username}: {error}')
        self._assign_role_to_user(user)

    def _delete_user(self, username: str):
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
            raise Keycloak.KeycloakError(f'User: {username} does not exist')

    def _get_user_realm_role(self, csvloader: CSVLoader, user_id: str) -> Union[str, None]:
        """get user's realm role

        Args:
            csvloader (CSVLoader): csvloder object
            user_id (str): user id

        Raises:
            Keycloak.KeycloakError: Exception raised for errors in the Keycloak

        Returns:
            Union[str, None]: role name or none if no found
        """
        for role in csvloader.template[Template.EXPORT][Template.EXPORT_ROLES]:
            try:
                for user in self.kc_admin.get_realm_role_members(role):
                    if user[Keycloak.Keycloak_API.ID] == user_id:
                        return role
            except exceptions.KeycloakGetError as error:
                raise Keycloak.KeycloakError(
                    f'Role: {role} does not exist in realm')
        return None

    @staticmethod
    def _filter_user(csvloader: CSVLoader, user: dict, rule: str) -> bool:
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
            name = csvloader.template[rule][Template.RULE_IDENTIFIER][Template.RULE_IDENTIFIER_NAME]
            return validator.validate({name: user[name]})
        except cerberus.schema.SchemaError as error:
            raise Keycloak.KeycloakError(f'Unknown rule: {error}')

    def _get_user(self, csvloader: CSVLoader, user_id: str, rule: str) -> Union[KCUser, None]:
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
            raise Keycloak.KeycloakError(
                f'Unable to find user id: f{user_id}: {error}')
        if Keycloak._filter_user(csvloader=csvloader, user=user, rule=rule):
            role = self._get_user_realm_role(
                csvloader=csvloader, user_id=user_id)
            attributes = dict(
                map(lambda attri: (attri[0], ''.join(attri[1])), user[Keycloak.Keycloak_API.ATTRIBUTES].items()))
            kcuser = KCUser(email=user[Keycloak.Keycloak_API.EMAIL], username=user[Keycloak.Keycloak_API.USERNAME],
                            firstname=user[Keycloak.Keycloak_API.FIRSTNAME], lastname=user[Keycloak.Keycloak_API.LASTNAME],
                            role=role, attributes=attributes)
            kcuser.createdtime = datetime.fromtimestamp(
                int(str(user[Keycloak.Keycloak_API.CREATEDTIME])[:10])).strftime('%d/%m/%y')
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
            user_flitered = self._get_user(csvloader=csvloader,
                                           user_id=user[Keycloak.Keycloak_API.ID], rule=rule)
            if user_flitered:
                logger.info(f'Get user {user_flitered.username}')
                list_users.append(user_flitered)
        return list_users

    @connect
    def delete_users(self, list_users: list):
        """delete users by giving list of users

        Args:
            list_users (list): list of users to be deleted
        """

        for user in list_users:
            self._delete_user(username=user.username)

    @connect
    def delete_all_users(self):
        """Delete all users from keycloak
        """
        for user in self.kc_admin.get_users():
            self._delete_user(username=user[Keycloak.Keycloak_API.USERNAME])

    @connect
    def add_users(self, users: list):
        """Add list of users to keycloak

        Args:
            users (list): A list of BM user instances
        """
        for user in users:
            self._add_user(user=user)
