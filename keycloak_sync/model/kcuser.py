import logging
from typing import Iterator

import coloredlogs
from keycloak_sync.abstract.user import User
from keycloak_sync.model.csvloader import CSVLoader
from pandas import Series

logger = logging.getLogger(__name__)


class KCUserError(Exception):
    """Exception raised for errors in the KCUser.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class KCUser(User):
    @staticmethod
    def set_log_level(level: str):
        """set KCUser log level

        Args:
            level (str): log level
        """
        coloredlogs.install(level=level, logger=logger)

    @staticmethod
    def _create_list_empty_users(csvloader: CSVLoader) -> list:
        """create a list of empty users by reading username column size

        Args:
            csvloader (CSVLoader): a Csvloader instance providing files

        Returns:
            list: list of empty users
        """
        username_label = csvloader.values["mapper"]["username"]
        return [KCUser() for _ in range(csvloader.data[username_label].size)]

    @staticmethod
    def _assign_parameters(csvloader: CSVLoader, list_users: list):
        """assign parameters for each user

        Args:
            csvloader (CSVLoader): a Csvloader instance providing files
            list_users (list): list of empty users

        Raises:
            KCUserError: Exception raised for errors in the KCUser
        """
        list_parameters = list(csvloader.values["mapper"].keys())
        for parameter in list_parameters:
            if not hasattr(KCUser, parameter):
                raise KCUserError(
                    f'mapper is not allowed to contain parameter: {parameter}')
            col = csvloader.values["mapper"][parameter]
            if parameter == 'attributes' and isinstance(col, list):
                list(map(lambda x: KCUser._assign_parameter_each_user(
                    parameter, csvloader.data[x.get('value')], list_users, key=x.get('key')), col))
            else:
                KCUser._assign_parameter_each_user(
                    parameter, csvloader.data[col], list_users)

    @ staticmethod
    def _set_user_parameter(parameter: str, iter_users: Iterator, key: str, value: str):
        """set one user's parameter

        Args:
            parameter (str): parameter name
            iter_users (Iterator): users iterator
            key (str): key used when parameter is 'attributes' 
            value (str): value used when parameter is 'attributes' 
        """
        user = next(iter_users)
        if parameter == 'attributes':
            if user.attributes is None:
                user.attributes = {}
            user.attributes[key] = value
        else:
            setattr(user, parameter, value)

    @ staticmethod
    def _assign_parameter_each_user(parameter: str, series: Series, list_users: list, key=None):
        """call _set_user_parameter to assign parameter for a list of users

        Args:
            parameter (str): parameter's name
            series (Series): one column in csv file
            list_users (list): list of users
            key ([type], optional): key used when parameter is 'attributes' 
        """
        iter_users = iter(list_users)
        series.map(lambda x: KCUser._set_user_parameter(
            parameter, iter_users, key, x))
        logger.info(f'Assign {parameter}  to users')

    @ staticmethod
    def _add_custom_attributes(csvloader: CSVLoader, list_users: list):
        """add custom attributes when is set in valeus file

        Args:
            csvloader (CSVLoader): a Csvloader instance providing files
            list_users (list): list of users

        Raises:
            KCUserError: Exception raised for errors in the KCUser
        """
        list_attributes = csvloader.values["custom_attributes"]
        if list_attributes:
            def assign_one_attribute(user: KCUser):
                """sub function used by map

                Args:
                    user (KCUser): a user instance

                Raises:
                    KCUserError: Exception raised for errors in the KCUser
                """
                for attribute in list_attributes:
                    try:
                        user.attributes[attribute['key']] = attribute['value']
                    except KeyError:
                        raise KCUserError(
                            f'custom_attributes only have attribute key and value.')
            list(map(assign_one_attribute, list_users))
            logger.info(f'Assign {list_attributes}  to users')

    @ staticmethod
    def create_list_users(csvloader: CSVLoader) -> list:
        """create list of users by loading csv file

        Args:
            csvloader (CSVLoader): a Csvloader instance providing files

        Returns:
            list: list of users
        """
        list_users = KCUser._create_list_empty_users(csvloader)
        KCUser._assign_parameters(
            csvloader=csvloader, list_users=list_users)
        KCUser._add_custom_attributes(csvloader, list_users)
        return list_users
