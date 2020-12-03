import logging
import cerberus
import coloredlogs
from datetime import datetime
from typing import Union
import pandas as pd
from keycloak import KeycloakAdmin, exceptions
from keycloak_sync.model.kcuser import KCUser
from keycloak_sync.model.csvloader import CSVLoader
logger = logging.getLogger(__name__)


class KeycloakError(Exception):
    """Exception raised for errors in the CSVLoader.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


def connect(func):
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
        coloredlogs.install(level=level, logger=logger)

    def _assign_role_to_user(self, user: KCUser):
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
    def add_user(self, user):
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
    def fliter_user(csvloader: CSVLoader, user: dict) -> bool:
        try:
            validator = cerberus.Validator(csvloader.load_export_identifier())
            name = csvloader.values["export_rules"]['identifier']['name']
            return validator.validate({name: user[name]})
        except cerberus.schema.SchemaError as error:
            raise KeycloakError(f'Unknown rule: {error}')

    def get_user(self, csvloader: CSVLoader, user_id: str) -> Union[KCUser, None]:
        try:
            user = self.kc_admin.get_user(user_id=user_id)
        except exceptions.KeycloakGetError as error:
            logger.error(f'Unable to find user id: f{user_id}: {error}')
            raise error
        if Keycloak.fliter_user(csvloader=csvloader, user=user):
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
    def get_users(self, csvloader: CSVLoader) -> list:
        logger.info(f"Use export schema: {csvloader.load_export_identifier()}")
        list_users = []
        for user in self.kc_admin.get_users():
            try:
                user = self.get_user(csvloader, user['id'])
                logger.info(f'Get user {user.username}')
                list_users.append(user)
            except exceptions.KeycloakGetError:
                raise KeycloakError(f'Skip user id: f{user["id"]}')
        return list_users
