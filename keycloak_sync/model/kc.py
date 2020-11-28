import pandas as pd
from keycloak import KeycloakAdmin, exceptions
from keycloak_sync.model.bmuser import BMuser
from keycloak_sync.model.log import logging
from datetime import datetime
logger = logging.getLogger(__name__)


class Keycloak:
    def __init__(self, server_url: str, client_id: str, realm_name: str, client_secret_key: str):
        try:
            self.kc_admin = KeycloakAdmin(server_url=server_url,
                                          client_id=client_id,
                                          realm_name=realm_name,
                                          client_secret_key=client_secret_key,
                                          verify=True)
        except exceptions.KeycloakConnectionError as error:
            logger.error(f'Unable connect to Keycloak {error}')
            raise error

    def add_user(self, user: BMuser):
        """Add user to keycloak

        Args:
            user (BMuser): A BM user instance

        Raises:
            error: exceptions.KeycloakGetError
            error: exceptions.KeycloakGetError
            error: exceptions.KeycloakGetError
        """
        user_id = self.kc_admin.get_user_id(username=user.username)
        if user_id:
            self.kc_admin.delete_user(user_id=user_id)
            logger.info(f'update user: {user.username}')
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
            role_id = self.kc_admin.get_realm_role(user.role)['id']
        except exceptions.KeycloakGetError as error:
            logger.error(f'Unable to get role {user.role}:{error}')
            raise error

        try:
            self.kc_admin.create_user(payload)
            user_id = self.kc_admin.get_user_id(username=user.username)
            logger.info(f'Add user: {user.username} successfully')
        except exceptions.KeycloakGetError as error:
            logger.error(f'Unable to create user {user.username}:{error}')
            raise error
        roles_info = [{
            'id': role_id,
            'name': user.role
        }]

        try:
            self.kc_admin.assign_realm_roles(user_id=user_id,
                                             client_id=self.kc_admin.client_id,
                                             roles=roles_info)
        except exceptions.KeycloakGetError as error:
            logger.error(
                f'Unable to assign user {user.username} with role {user.role} :{error}')
            raise error

    def add_users(self, users: list):
        """Add list of users to keycloak

        Args:
            users (list): A list of BM user instances
        """
        for user in users:
            try:
                self.add_user(user)
            except exceptions.KeycloakGetError:
                logger.error(
                    f'Unable to finish add {user.username}, skipped this user')

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
        for role in BMuser.AVAILABLE_ROLES:
            try:
                for user in self.kc_admin.get_realm_role_members(role):
                    if user['id'] == user_id:
                        return role
            except exceptions.KeycloakGetError as error:
                logger.error(f'Role: {role} does not exist in realm: {error}')
        return None

    def get_user(self, user_id: str) -> BMuser:
        try:
            user = self.kc_admin.get_user(user_id=user_id)
            createdtime = datetime.fromtimestamp(
                int(str(user['createdTimestamp'])[:10])).strftime('%d/%m/%y')
            role = self.get_user_realm_role(user_id=user_id)
            userattri = {}
            userattri['Client Full Name'] = BMuser.ATTRIBUTES['Client Full Name']
            userattri['Client Short Name'] = BMuser.ATTRIBUTES['Client Short Name']
            userattri['Subsidiary Code'] = user['attributes']['Subsidiary Code'].pop()
            userattri['Subsidiary Name'] = user['attributes']['Subsidiary Name'].pop()
            bmuser = BMuser(email=user['email'], username=user['username'],
                            firstname=user['firstName'], lastname=user['lastName'],
                            role=role, attributes=userattri)
            bmuser.createdtime = createdtime
        except exceptions.KeycloakGetError as error:
            logger.error(f'Unable to find user id: f{user_id}: {error}')
            raise error
        return bmuser

    def get_users(self) -> list:
        list_users = []
        for user in self.kc_admin.get_users():
            try:
                list_users.append(self.get_user(user['id']))
            except exceptions.KeycloakGetError:
                logger.error(f'Skip user id: f{user_id}')
        return list_users
