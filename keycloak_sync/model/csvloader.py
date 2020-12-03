import cerberus
import pandas as pd
import yaml
from keycloak_sync.abstract.loader import Loader


class CSVLoaderError(Exception):
    """Exception raised for errors in the CSVLoader.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class CSVLoader(Loader):
    def __init__(self, values, file):
        try:
            with open(values, 'r') as stream:
                self._values = yaml.safe_load(stream)
            separator = self._values["separator"]
            header = self._values["header"]
            self._data = pd.read_csv(filepath_or_buffer=file,
                                     sep=separator, header=header, skip_blank_lines=True)
        except (TypeError, FileNotFoundError):
            raise CSVLoaderError(f'File path does not exist')

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
    def _to_schema(value) -> dict:
        try:
            name = value["name"]
            del value["name"]
            return {name: value}
        except KeyError:
            raise CSVLoaderError(f'data_model should contains label: name')

    @staticmethod
    def _format_series_to_schema(series) -> list:
        def to_formatted(series, data):
            if pd.isnull(data):
                data = None
            return {series.name: data}
        return list(series.map(lambda x: to_formatted(series, x)))

    @staticmethod
    def _find_schema(schema_list, schema_name) -> dict:
        for schema in schema_list:
            if list(schema.keys())[0] == schema_name:
                return schema

    def valide_schemas(self):
        try:
            schemas = self._values["data_model"]
            cols = self._data.columns.tolist()
            schemas_names = list(map(lambda x: x["name"], schemas))
            schema_list = list(map(CSVLoader._to_schema, schemas))
        except KeyError as error:
            raise CSVLoaderError(
                f'Values file should contain label: name in data_model')
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
