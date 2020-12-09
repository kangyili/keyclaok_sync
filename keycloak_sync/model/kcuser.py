import logging
from typing import Iterator

import coloredlogs
from keycloak_sync.abstract_model.user import User
from keycloak_sync.model.csvloader import CSVLoader, Template
from pandas import Series

logger = logging.getLogger(__name__)


class KCUser(User):

    class KCUserError(Exception):
        """Exception raised for errors in the KCUser.

        Attributes:
            message -- explanation of the error
        """

        def __init__(self, message):
            self.message = message

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
        username = csvloader.template[Template.MAPPER][Template.MAPPER_USERNAME]
        return [KCUser() for _ in range(csvloader.data[username].size)]

    @ staticmethod
    def _set_parameter(parameter: str, iter_users: Iterator, key: str, value: str):
        """set one user's parameter

        Args:
            parameter (str): parameter name
            iter_users (Iterator): users iterator
            key (str): key used when parameter is 'attributes' 
            value (str): value used when parameter is 'attributes' 
        """
        user = next(iter_users)
        if parameter == Template.MAPPER_ATTRIBUTES:
            if user.attributes is None:
                user.attributes = {}
            user.attributes[key] = value
        else:
            setattr(user, parameter, value)

    @ staticmethod
    def _assign_parameter_to_user(parameter: str, series: Series, list_users: list, key=None):
        """call _set_parameter to assign parameter for a list of users

        Args:
            parameter (str): parameter's name
            series (Series): one column in csv file
            list_users (list): list of users
            key ([type], optional): key used when parameter is 'attributes' 
        """
        iter_users = iter(list_users)
        series.map(lambda value: KCUser._set_parameter(
            parameter, iter_users, key, value))
        logger.info(f'Assign {parameter}  to users')

    @staticmethod
    def _assign_parameters_to_list_users(csvloader: CSVLoader, list_users: list):
        """assign parameters for each user

        Args:
            csvloader (CSVLoader): a Csvloader instance providing files
            list_users (list): list of empty users

        Raises:
            KCUserError: Exception raised for errors in the KCUser
        """
        list_parameters = list(csvloader.template[Template.MAPPER].keys())
        for parameter in list_parameters:
            if not hasattr(KCUser, parameter):
                raise KCUser.KCUserError(
                    f'mapper is not allowed to contain parameter: {parameter}')
            column_name = csvloader.template[Template.MAPPER][parameter]
            if parameter == Template.MAPPER_ATTRIBUTES and isinstance(column_name, list):
                for column_name_ in column_name:
                    KCUser._assign_parameter_to_user(
                        parameter=parameter, series=csvloader.data[column_name_.get(Template.MAPPER_ATTRIBUTES_VALUE)], list_users=list_users, key=column_name_.get(Template.MAPPER_ATTRIBUTES_KEY))
            else:
                KCUser._assign_parameter_to_user(
                    parameter, csvloader.data[column_name], list_users)

    @ staticmethod
    def _add_custom_attributes(csvloader: CSVLoader, list_users: list):
        """add custom attributes when is set in valeus file

        Args:
            csvloader (CSVLoader): a Csvloader instance providing files
            list_users (list): list of users

        Raises:
            KCUserError: Exception raised for errors in the KCUser
        """
        list_attributes = csvloader.template[Template.CUSTOM_ATTRIBUTES]
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
                        raise KCUser.KCUserError(
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
        KCUser._assign_parameters_to_list_users(
            csvloader=csvloader, list_users=list_users)
        KCUser._add_custom_attributes(csvloader, list_users)
        return list_users
