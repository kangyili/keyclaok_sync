import logging
import coloredlogs
from datetime import datetime
import pandas as pd
from keycloak import KeycloakAdmin, exceptions
from keycloak_sync.model.kcuser import KCUser
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

    def delete_user(self, username: str) -> bool:
        """Delete a user from keycloak

        Args:
            username (str): user index

        Returns:
            bool: Success is True, otherwise is False
        """
        user_id = self.kc_admin.get_user_id(username=username)
        try:
            assert user_id
            self.kc_admin.delete_user(user_id=user_id)
            logger.info(f'Delete user: {username}')
            return True
        except AssertionError:
            logger.warning(f'User: {username} does not exist')
            return False

    def delete_users(self):
        """Delete all users from keycloak
        """
        for user in self.kc_admin.get_users():
            try:
                assert self.delete_user(username=user['username'])
            except AssertionError:
                logger.warning(f'Skip User: {user["username"]}')

    def get_user_realm_role(self, user_id: str):
        for role in list(map(lambda x: x['name'], self.kc_admin.get_realm_roles())):
            try:
                for user in self.kc_admin.get_realm_role_members(role):
                    if user['id'] == user_id:
                        return role
            except exceptions.KeycloakGetError as error:
                logger.error(f'Role: {role} does not exist in realm: {error}')
        return None

    def get_user(self, user_id: str) -> KCUser:
        try:
            user = self.kc_admin.get_user(user_id=user_id)
            createdtime = datetime.fromtimestamp(
                int(str(user['createdTimestamp'])[:10])).strftime('%d/%m/%y')
            # print(createdtime)
            role = self.get_user_realm_role(user_id=user_id)
            # print(user['username']+'--->'+role)
            attributes = dict(
                map(lambda item: (item[0], ''.join(item[1])), user['attributes'].items()))
            # print(attributes)
            kcuser = KCUser(email=user['email'], username=user['username'],
                            firstname=user['firstName'], lastname=user['lastName'],
                            role=role, attributes=attributes)
            kcuser.createdtime = createdtime
        except exceptions.KeycloakGetError as error:
            logger.error(f'Unable to find user id: f{user_id}: {error}')
            raise error
        return kcuser

    @connect
    def get_users(self) -> list:
        list_users = []
        for user in self.kc_admin.get_users():
            try:
                print(user['id'])
                x = self.get_user(user['id'])
                print(x.username+'--->'+x.role)
                list_users.append(x)
            except exceptions.KeycloakGetError:
                logger.error(f'Skip user id: f{user["id"]}')
        print(len(list_users))
        return list_users
