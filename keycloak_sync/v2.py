import logging
import sys
from pathlib import Path

import click
import coloredlogs

from keycloak_sync.model.csvloader import CSVLoader, CSVLoaderError
from keycloak_sync.model.kc import Keycloak, KeycloakError
from keycloak_sync.model.kcuser import KCUser, KCUserError

logger = logging.getLogger(__name__)


class Arguments:
    LEVEL_WARNING = 'WARNING'
    LEVEL_DEBUG = 'DEBUG'
    BUCKET = 'bucket'
    BUCKET_PATH = 'bucket_path'
    BUCKET_NAME = 'bucket_name'
    KEYCLOAK_SERVER_URL = 'keycloak_server_url'
    KEYCLOAK_CLIENT_ID = 'keycloak_client_id'
    KEYCLOAK_REALM_NAME = 'keycloak_realm_name'
    KEYCLOAK_CLIENT_SECRET = 'keycloak_client_secret'
    CSV_FILE_NAME = 'csv_file_name'
    CSV_FILE_VALUES = 'csv_file_values'


@click.group()
@click.option('--debug/--no-debug', default=False, help='Turn on log in terminal')
def kcctl(debug):
    """Keycloak command line tool"""
    level = Arguments.LEVEL_WARNING
    if debug:
        level = Arguments.LEVEL_DEBUG
    coloredlogs.install(level=level, logger=logger)
    Keycloak.set_log_level(level)


@kcctl.command()
@click.option('--kc-url', Arguments.KEYCLOAK_SERVER_URL, envvar=Arguments.KEYCLOAK_SERVER_URL.upper(), required=True, help='Keycloak server url')
@click.option('--kc-realm', Arguments.KEYCLOAK_REALM_NAME, envvar=Arguments.KEYCLOAK_REALM_NAME.upper(), required=True, help='Keycloak realm name')
@click.option('--kc-clt', Arguments.KEYCLOAK_CLIENT_ID, envvar=Arguments.KEYCLOAK_CLIENT_ID.upper(), required=True, help='keycloak client name')
@click.option('--kc-clt-sct', Arguments.KEYCLOAK_CLIENT_SECRET, envvar=Arguments.KEYCLOAK_CLIENT_SECRET.upper(), required=True, help='Keycloak cleint secret')
@click.option('-f', '--file', Arguments.CSV_FILE_NAME, envvar=Arguments.CSV_FILE_NAME.upper(), required=True, help='Csv file path')
@click.option('-v', '--values', Arguments.CSV_FILE_VALUES, envvar=Arguments.CSV_FILE_VALUES.upper(), required=True, help='Custom values file')
def sync(**kwargs):
    """Synchronize users from CSV file to keycloak"""
    try:
        csvloader = CSVLoader(values=kwargs.get(
            Arguments.CSV_FILE_VALUES), file=kwargs.get(Arguments.CSV_FILE_NAME))
        csvloader.valide_schemas()
        logger.info(f"CSV file is valid")
        list_users = KCUser.create_list_users(csvloader)
        logger.info(f"Create User Object")
        kc = Keycloak(server_url=kwargs.get(Arguments.KEYCLOAK_SERVER_URL),
                      client_id=kwargs.get(Arguments.KEYCLOAK_CLIENT_ID),
                      realm_name=kwargs.get(Arguments.KEYCLOAK_REALM_NAME),
                      client_secret_key=kwargs.get(Arguments.KEYCLOAK_CLIENT_SECRET))
        kc.add_users(list_users)
    except (CSVLoaderError, KCUserError, KeycloakError) as error:
        logger.error(error)
        sys.exit(1)
