from typing import Iterator
import logging
from keycloak_sync.abstract.user import User
from keycloak_sync.model.csvloader import CSVLoader
from pandas import Series
import coloredlogs
logger = logging.getLogger(__name__)


class CSVLoaderError(Exception):
    """Exception raised for errors in the CSVLoader.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


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
        coloredlogs.install(level=level, logger=logger)

    @staticmethod
    def _create_list_empty_users(csvloader: CSVLoader):
        username_label = csvloader.values["mapper"]["username"]
        return [KCUser() for _ in range(csvloader.data[username_label].size)]

    @staticmethod
    def _assign_parameters(csvloader: CSVLoader, list_users: list):
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
        user = next(iter_users)
        if parameter == 'attributes':
            if user.attributes is None:
                user.attributes = {}
            user.attributes[key] = value
        else:
            setattr(user, parameter, value)

    @ staticmethod
    def _assign_parameter_each_user(parameter: str, series: Series, list_users: list, key=None):
        iter_users = iter(list_users)
        series.map(lambda x: KCUser._set_user_parameter(
            parameter, iter_users, key, x))
        logger.info(f'Assign {parameter}  to users')

    @ staticmethod
    def _add_custom_attributes(csvloader: CSVLoader, list_users: list):
        list_attributes = csvloader.values["custom_attributes"]

        def assign_one_attribute(user: KCUser):
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
        list_users = KCUser._create_list_empty_users(csvloader)
        KCUser._assign_parameters(
            csvloader=csvloader, list_users=list_users)
        KCUser._add_custom_attributes(csvloader, list_users)
        return list_users
