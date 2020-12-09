import logging
from logging import log
from typing import Union
import cerberus
import coloredlogs
import pandas as pd
import numpy as np
import yaml
from keycloak_sync.abstract_model.loader import Loader
from pathlib import Path
logger = logging.getLogger(__name__)


class Template(Loader):
    FORMAT = 'format'
    SEPARATOR = 'separator'
    HEADER = 'header'
    DATA_MODEL = 'data_model'
    DATA_MODEL_NAME = 'name'
    MAPPER = 'mapper'
    MAPPER_USERNAME = "username"
    MAPPER_ATTRIBUTES = 'attributes'
    MAPPER_ATTRIBUTES_KEY = 'key'
    MAPPER_ATTRIBUTES_VALUE = 'value'
    CUSTOM_ATTRIBUTES = 'custom_attributes'
    RULE_IDENTIFIER = 'identifier'
    RULE_IDENTIFIER_NAME = 'name'
    EXPORT = 'export_rules'
    EXPORT_SEPARATOR = 'separator'
    EXPORT_HEADER = 'header'
    EXPORT_MAPPER = 'mapper'
    EXPORT_ROLES = 'available_roles'


class CSVLoader(Loader):
    """Load CSV file and template file

    Args:
        Loader (object): a basic loader
    """
    FILE_FORMAT = 'CSV'

    class CSVLoaderError(Exception):
        """Exception raised for errors in the CSVLoader.

        Attributes:
            message -- explanation of the error
        """

        def __init__(self, message):
            self.message = message

    def __init__(self, template: Path, csvfile: Union[Path, None]):
        self._load_template(template=template)
        self._load_csvfile(csvfile=csvfile)

    @property
    def data(self):
        return self._data

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, template):
        self._template = template

    @data.setter
    def data(self, data):
        self._data = data

    def _load_template(self, template: Path):
        """Loader template file

        Args:
            template (str): template file path

        Raises:
            CSVLoader.CSVLoaderError: [description]
        """
        try:
            with open(template, 'r') as stream:
                self._template = yaml.safe_load(stream)
        except (TypeError, FileNotFoundError):
            raise CSVLoader.CSVLoaderError(
                f'template file path does not exist')

    def _load_csvfile(self, csvfile: Union[Path, None]):
        if csvfile is not None:
            try:
                separator = self._template[Template.SEPARATOR]
                header = self._template[Template.HEADER]
                self._data = pd.read_csv(filepath_or_buffer=csvfile,
                                         sep=separator, header=header, skip_blank_lines=True)
                self._data = self._data.replace({np.nan: None})
            except (TypeError, FileNotFoundError):
                raise CSVLoader.CSVLoaderError(f'CSV File path does not exist')

    @staticmethod
    def set_log_level(level: str):
        """Set log level

        Args:
            level (str): log's level
        """
        coloredlogs.install(level=level, logger=logger)

    @staticmethod
    def _get_column_schema_from_data_model(data_model: dict) -> dict:
        """get a column schema

        Args:
            data_model (dict): define column's schema

        Raises:
            CSVLoader.CSVLoaderError: Exception raised for errors in the CSVLoader

        Returns:
            dict: schema which can be used bt cerberus
        """
        try:
            name = data_model[Template.DATA_MODEL_NAME]
            schema = {}
            for rule_name, rule in data_model.items():
                if rule_name != Template.DATA_MODEL_NAME:
                    schema[rule_name] = rule
            return {name: {'type': 'list', 'schema': schema}}
        except KeyError:
            raise CSVLoader.CSVLoaderError(
                f'data_model should contains label: name')

    @staticmethod
    def _change_column_to_dict(column: pd.Series) -> dict:
        """change one column into dictionary

        Args:
            column (pd.Series): one column serie

        Returns:
            dict: dictionary with {column name: column values list}
        """
        return {column.name: column.tolist()}

    @staticmethod
    def _validate_column(column: pd.Series, column_schema: dict):
        """validate one column

        Args:
            column (pd.Series): one column serie
            column_schema (dict): column schema used by cerberus

        Raises:
            CSVLoader.CSVLoaderError: Exception raised for errors in the CSVLoader
        """
        try:
            validator = cerberus.Validator(column_schema)
        except cerberus.schema.SchemaError as error:
            raise CSVLoader.CSVLoaderError(f'Unknown rule: {error}')
        if validator.validate(CSVLoader._change_column_to_dict(column)):
            logger.info(f'Column: {column.name} is valid')
        else:
            error_value = validator._errors[0].info[0][0].value
            raise CSVLoader.CSVLoaderError(
                f'Value: {error_value} in column :{column.name}is invalid')

    @staticmethod
    def _check_data_model(data_model: dict, column_names: list) -> bool:
        """check data model is valid or not

        Args:
            data_model (dict): read from template file
            column_names (list): list of column's names in csv file

        Raises:
            CSVLoader.CSVLoaderError: Exception raised for errors in the CSVLoader

        Returns:
            bool: true is valide otherwise is false
        """
        try:
            data_model_name = data_model[Template.DATA_MODEL_NAME]
        except KeyError:
            raise CSVLoader.CSVLoaderError(
                'template file should contain label: data_model.name')
        if data_model_name in column_names:
            return True
        else:
            return False

    @staticmethod
    def _read_users_into_dataframe(key: str, value: Union[list, str], list_users: list, dataframe: dict):
        """read users object into dataframe

        Args:
            key (str): each column name responding a user's parameter
            value (str/list): column name
            list_users (list): list of users
            dataframe (dict): used for transforming in to csv
        """
        if key == Template.MAPPER_ATTRIBUTES:
            for attribute in value:
                dataframe[attribute[Template.MAPPER_ATTRIBUTES_VALUE]] = []
                list(map(lambda user: dataframe[attribute[Template.MAPPER_ATTRIBUTES_VALUE]].append(
                    user.attributes[attribute[Template.MAPPER_ATTRIBUTES_KEY]]), list_users))
        else:
            dataframe[value] = []
            for user in list_users:
                dataframe[value].append(getattr(user, key))

    def validate(self):
        """validate csv file

        Raises:
            CSVLoader.CSVLoaderError: Exception raised for errors in the CSVLoader
        """
        if not self._template[Template.FORMAT].upper() == CSVLoader.FILE_FORMAT:
            raise CSVLoader.CSVLoaderError('Only support CSV file')
        try:
            data_models = self._template[Template.DATA_MODEL]
            column_names = self._data.columns.tolist()
        except KeyError as error:
            raise CSVLoader.CSVLoaderError(
                'template file should contain label: data_model')
        for data_model in data_models:
            if CSVLoader._check_data_model(data_model=data_model, column_names=column_names):
                column_schema = CSVLoader._get_column_schema_from_data_model(
                    data_model)
                column_name = data_model[Template.DATA_MODEL_NAME]
                CSVLoader._validate_column(
                    column=self._data[column_name], column_schema=column_schema)
            else:
                raise CSVLoader.CSVLoaderError(
                    f"Column {data_model[Template.DATA_MODEL_NAME]} does not exist in file")

    def load_identifier(self, rule: str) -> dict:
        """loader identifier to fliter users

        Args:
            rule (str): export or delete

        Raises:
            CSVLoader.CSVLoaderError: Exception raised for errors in the CSVLoader

        Returns:
            dict: a shema used by cerberus
        """
        if self._template[rule]:
            if self._template[rule][Template.RULE_IDENTIFIER]:
                name = self._template[rule][Template.RULE_IDENTIFIER][Template.RULE_IDENTIFIER_NAME]
                rules = {}
                for rule_name, rule in self._template[rule][Template.RULE_IDENTIFIER].items():
                    if rule_name != Template.RULE_IDENTIFIER_NAME:
                        rules[rule_name] = rule
                return {name: rules}
            else:
                raise CSVLoader.CSVLoaderError(
                    f'Export_rules file should contains identifier to fliter users')
        else:
            raise CSVLoader.CSVLoaderError(
                f'template file should contains {rule}')

    def export_users_to_csv(self, list_users: list, export_path: str):
        """export users object to csv

        Args:
            list_users (list): list of users
            export_path (str): path where csv file in
        """
        dataframe = {}
        list_mapper = self._template[Template.EXPORT][Template.EXPORT_MAPPER]
        for user_parameter, column_name in list_mapper.items():
            CSVLoader._read_users_into_dataframe(
                user_parameter, column_name, list_users, dataframe)
        pd.DataFrame(data=dataframe).to_csv(
            path_or_buf=export_path, sep=self._template[Template.EXPORT][Template.EXPORT_SEPARATOR], header=self._template[Template.EXPORT][Template.EXPORT_HEADER], index=False)
