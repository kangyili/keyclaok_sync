import logging
from logging import log

import cerberus
import coloredlogs
import pandas as pd
import yaml
from keycloak_sync.abstract.loader import Loader

logger = logging.getLogger(__name__)


class CSVLoaderError(Exception):
    """Exception raised for errors in the CSVLoader.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class CSVLoader(Loader):
    """Load CSV file and values file

    Args:
        Loader (object): a basic loader
    """

    def __init__(self, values, file=None):
        if values:
            try:
                with open(values, 'r') as stream:
                    self._values = yaml.safe_load(stream)
            except (TypeError, FileNotFoundError):
                raise CSVLoaderError(f'Values file path does not exist')
            if file:
                try:
                    separator = self._values["separator"]
                    header = self._values["header"]
                    self._data = pd.read_csv(filepath_or_buffer=file,
                                             sep=separator, header=header, skip_blank_lines=True)
                    self.format = 'CSV'
                except (TypeError, FileNotFoundError):
                    raise CSVLoaderError(f'CSV File path does not exist')
        else:
            raise CSVLoaderError(f'Values file is nessecary')

    @staticmethod
    def set_log_level(level: str):
        """Set log level

        Args:
            level (str): log's level
        """
        coloredlogs.install(level=level, logger=logger)

    @property
    def data(self):
        return self._data

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, values):
        self._values = values

    @data.setter
    def data(self, data):
        self._data = data

    @staticmethod
    def _to_schema(value: dict) -> dict:
        """Change a dict into schema 

        Args:
            value ([dict]): define column's rule

        Raises:
            CSVLoaderError: Custom CSVLoader type error

        Returns:
            dict: schema which can be used bt cerberus
        """
        try:
            name = value["name"]
            del value["name"]
            return {name: value}
        except KeyError:
            raise CSVLoaderError(f'data_model should contains label: name')

    @staticmethod
    def _format_series_to_schema(series: pd.Series) -> list:
        """change pandas.series type in to list of dictionary

        Args:
            series (pd.Series): a column in csv file

        Returns:
            list: list of dictionary waiting to be valided
        """
        def to_formatted(series: pd.Series, data: str) -> dict:
            """sub function used by map

            Args:
                series (pd.Series): a column
                data (str): each value in this column

            Returns:
                dict: key value pair defined by column's name and each value in column
            """
            if pd.isnull(data):
                data = None
            return {series.name: data}
        return list(series.map(lambda x: to_formatted(series, x)))

    @staticmethod
    def _find_schema(schema_list: list, schema_name: str) -> dict:
        """find schema from values file

        Args:
            schema_list (list): list of schema read from values
            schema_name (str): needed schema name

        Returns:
            dict: schema needed
        """
        for schema in schema_list:
            if list(schema.keys())[0] == schema_name:
                return schema

    @staticmethod
    def _setup_column(key: str, value: str, list_users: list, dataframe: dict):
        """set up each column for exporting

        Args:
            key (str): each column name responding a user's parameter
            value (str): column name
            list_users (list): list of users
            dataframe (dict): used for transforming in to csv
        """
        if key == 'attributes':
            for attribute in value:
                dataframe[attribute['value']] = []
                list(map(lambda x: dataframe[attribute['value']].append(
                    x.attributes[attribute['key']]), list_users))
        else:
            dataframe[value] = []
            list(map(lambda x: dataframe[value].append(
                getattr(x, key)), list_users))

    def valide_schemas(self):
        """valide csv file

        Raises:
            CSVLoaderError: csv file is invalide
        """
        if not self._values["format"].upper() == self.format:
            raise CSVLoaderError('Only support CSV file')
        try:
            schemas = self._values["data_model"]
            cols = self._data.columns.tolist()
            schemas_names = list(map(lambda x: x["name"], schemas))
            schema_list = list(map(CSVLoader._to_schema, schemas))
        except KeyError as error:
            raise CSVLoaderError(
                'Values file should contain label: name in data_model')
        for schema_name in schemas_names:
            if schema_name in cols:
                schema = CSVLoader._find_schema(schema_list, schema_name)
                try:
                    validator = cerberus.Validator(schema)
                except cerberus.schema.SchemaError as error:
                    raise CSVLoaderError(f'Unknown rule: {error}')
                list_data = CSVLoader._format_series_to_schema(
                    self._data[schema_name])
                error_line = 0
                for result in list(map(validator.validate, list_data)):
                    error_line += 1
                    if not result:
                        raise CSVLoaderError(
                            f"Column: {schema_name} is invalid in line : {error_line}")
            else:
                raise CSVLoaderError(
                    f"Column: {schema_name} does not exist in CSV file")
            logger.info(f'Column: {schema_name} is Valided')

    def load_identifier(self, rule: str) -> dict:
        """loader identifier to fliter users

        Args:
            rule (str): export or delete

        Raises:
            CSVLoaderError: un able to load identifier

        Returns:
            dict: a shema used by cerberus
        """
        if self._values[rule]:
            if self._values[rule]['identifier']:
                name = self._values[rule]['identifier']['name']
                rules = {k: v for k, v in self._values[rule]['identifier'].items() if k not in {
                    'name': name}}
                return {name: rules}
            else:
                raise CSVLoaderError(
                    f'Export_rules file should contains identifier to fliter users')
        else:
            raise CSVLoaderError(f'Values file should contains export_rules')

    def export_users_to_csv(self, list_users: list, export_path: str):
        """export users object to csv

        Args:
            list_users (list): list of users
            export_path (str): path where csv file in
        """
        dataframe = {}
        list_mapper = self._values["export_rules"]["mapper"]
        list(map(lambda x: CSVLoader._setup_column(
            x[0], x[1], list_users, dataframe), list_mapper.items()))
        pd.DataFrame(data=dataframe).to_csv(
            path_or_buf=export_path, sep=self._values["export_rules"]["separator"], header=self._values["export_rules"]["header"], index=False)
