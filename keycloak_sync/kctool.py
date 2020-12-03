"""
A command line tool aimed to synchronize and export users on keycloak.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import coloredlogs
from keycloak import exceptions

from keycloak_sync.model.bmcsvfile import BMcsvfile
from keycloak_sync.model.csvloader import CSVLoader, CSVLoaderError
from keycloak_sync.model.kc import Keycloak, KeycloakError
from keycloak_sync.model.kcuser import KCUser, KCUserError

logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)


class KCtool:
    """Keycloak command line tool
    """

    class Arguments:
        BUCKET = 'bucket'
        BUCKET_PATH = 'bucket_path'
        BUCKET_NAME = 'bucket_name'
        KEYCLOAK_SERVER_URL = 'keycloak_server_url'
        KEYCLOAK_CLIENT_ID = 'keycloak_client_id'
        KEYCLOAK_REALM_NAME = 'keycloak_realm_name'
        KEYCLOAK_CLIENT_SECRET = 'keycloak_client_secret'
        CSV_FILE_NAME = 'csv_file_name'
        CSV_FILE_VALUES = 'csv_file_values'

    def __init__(self):

        parser = argparse.ArgumentParser(
            description="keycloak synchronize tool",
            usage="""keycloak <command> [<args>]
The most commonly used keycloak commands are:
sync    synchronize users to keycloak
syncbk  synchronize users to keycloak from google strage bucket
export  export users from keycloak
purge   Purage users on keycloak
            """,
        )
        parser.add_argument("command", help="Subcommand to run")
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print("Unrecognized command")
            parser.print_help()
            sys.exit(1)
        getattr(self, args.command)()

    @classmethod
    def __setdefault__(cls, parser: object):
        """set default parameters for connecting keycloak server

        Args:
            parser (object): shared with a parent command
        """
        parser.add_argument(
            "--kc-url",
            default=None,
            dest=KCtool.Arguments.KEYCLOAK_SERVER_URL,
            help="Keycloak server url",
        )
        parser.add_argument(
            "--kc-realm",
            default=None,
            dest=KCtool.Arguments.KEYCLOAK_REALM_NAME,
            help="Keycloak realm name",
        )
        parser.add_argument(
            "--kc-clt",
            default=None,
            dest=KCtool.Arguments.KEYCLOAK_CLIENT_ID,
            help="keycloak client name",
        )
        parser.add_argument(
            "--kc-clt-sct",
            default=None,
            dest=KCtool.Arguments.KEYCLOAK_CLIENT_SECRET,
            help="Keycloak cleint secret",
        )

    @classmethod
    def __setbucket__(cls, parser: object):
        parser.add_argument(
            "--bk-name",
            default=None,
            dest=KCtool.Arguments.BUCKET_NAME,
            help="Cloud Strage Bucket name",
        )
        parser.add_argument(
            "--bk-path",
            default=None,
            dest=KCtool.Arguments.BUCKET_PATH,
            help="Cloud Strage Bucket path",
        )

    def sync(self):
        """synchronize users
        """
        parser = argparse.ArgumentParser(
            description="Synchronize users on keycloak")
        KCtool.__setdefault__(parser)
        parser.add_argument(
            "-f",
            "--file",
            default=None,
            dest=KCtool.Arguments.CSV_FILE_NAME,
            help="Csv file path")
        parser.add_argument(
            "-v",
            "--values",
            default=None,
            dest=KCtool.Arguments.CSV_FILE_VALUES,
            help="Custom CSV file values")

        args = parser.parse_args(sys.argv[2:])
        csv_file_name = getattr(
            args, KCtool.Arguments.CSV_FILE_NAME) or os.getenv(
            KCtool.Arguments.CSV_FILE_NAME.upper())
        csv_file_values = getattr(
            args, KCtool.Arguments.CSV_FILE_VALUES) or os.getenv(
            KCtool.Arguments.CSV_FILE_VALUES.upper())
        keycloak_server_url = getattr(
            args, KCtool.Arguments.KEYCLOAK_SERVER_URL) or os.getenv(
            KCtool.Arguments.KEYCLOAK_SERVER_URL.upper())
        keycloak_realm_name = getattr(
            args, KCtool.Arguments.KEYCLOAK_REALM_NAME) or os.getenv(
            KCtool.Arguments.KEYCLOAK_REALM_NAME.upper())
        keycloak_client_id = getattr(
            args, KCtool.Arguments.KEYCLOAK_CLIENT_ID) or os.getenv(
            KCtool.Arguments.KEYCLOAK_CLIENT_ID.upper())
        keycloak_client_secret = getattr(
            args, KCtool.Arguments.KEYCLOAK_CLIENT_SECRET) or os.getenv(
            KCtool.Arguments.KEYCLOAK_CLIENT_SECRET.upper())

        if (csv_file_name is None or csv_file_values is None or
            keycloak_server_url is None or keycloak_realm_name is None or
                keycloak_client_id is None or keycloak_client_secret is None):
            logger.error('Missing parameters')
            parser.print_help()
            sys.exit(1)

        try:
            csvloader = CSVLoader(values=csv_file_values, file=csv_file_name)
            csvloader.valide_schemas()
            logger.info(f"CSV file is valid")
            list_users = KCUser.create_list_users(csvloader)
            logger.info(f"Create User Object")
            kc = Keycloak(server_url=keycloak_server_url,
                          client_id=keycloak_client_id,
                          realm_name=keycloak_realm_name,
                          client_secret_key=keycloak_client_secret)
            kc.add_users(list_users)
        except (CSVLoaderError, KCUserError, KeycloakError) as error:
            logger.error(error)
            parser.print_help()
            sys.exit(1)

        # try:
        #     kc = Keycloak(server_url=self.config['DEFAULT']['KEYCLOAK_SERVER_URL'],
        #                   client_id=self.config['DEFAULT']['KEYCLOAK_CLIENT_ID'],
        #                   realm_name=self.config['DEFAULT']['KEYCLOAK_REALM_NAME'],
        #                   client_secret_key=self.config['DEFAULT']['KEYCLOAK_CLIENT_SECRET'])
        #     if bmcsvfile.isformat():
        #         list_users = bmcsvfile.readcsv2users()
        #         kc.add_users(users=list_users)
        #     else:
        #         logger.error('Invalid CSV file')
        #         sys.exit(1)
        # except (exceptions.KeycloakGetError, exceptions.KeycloakConnectionError, FileNotFoundError):
        #     logger.error('Unable Synchronize')
        #     parser.print_help()
        #     sys.exit(1)

    def syncbk(self):
        """synchronize users from buckets
        """
        parser = argparse.ArgumentParser(
            description="Synchronize users on keycloak from Google Storage Bucket")
        KCtool.__setdefault__(parser)
        KCtool.__setbucket__(parser)
        parser.add_argument(
            "-f", "--file", default=None, dest="csv_file", help="Csv file name"
        )
        args = parser.parse_args(sys.argv[2:])
        self.__parsedefault__(args)
        bucket_name = args.BUCKET_NAME or os.getenv(
            KCtool.Arguments.BUCKET_NAME.upper())
        bucket_path = args.BUCKET_PATH or os.getenv(
            KCtool.Arguments.BUCKET_PATH.upper())
        # self.config["SYNC-BUCKET"]["CSV_FILE"] = args.CSV_FILE or os.getenv(
        #     "CSV_FILE", "None"
        # )

    def export(self):
        """export users from keycloak
        """
        parser = argparse.ArgumentParser(
            description="Export users from keycloak")
        KCtool.__setdefault__(parser)
        parser.add_argument(
            "-d",
            "--dest",
            default=None,
            dest="CSV_FILE_PATH",
            help="Csv file path")
        parser.add_argument(
            "--sp", default=None, dest="CSV_FILE_SP", help="Csv file sparator"
        )
        args = parser.parse_args(sys.argv[2:])
        self.__parsedefault__(args)
        # self.config["EXPORT-LOCAL"]["CSV_FILE_PATH"] = args.CSV_FILE_PATH or os.getenv(
        #     "CSV_FILE_PATH", "./output.csv")
        # self.config["EXPORT-LOCAL"]["CSV_FILE_SP"] = args.CSV_FILE_SP or os.getenv(
        #     "CSV_FILE_SP", ";")

        # try:
        #     kc = Keycloak(
        #         server_url=self.config['DEFAULT']['KEYCLOAK_SERVER_URL'],
        #         client_id=self.config['DEFAULT']['KEYCLOAK_CLIENT_ID'],
        #         realm_name=self.config['DEFAULT']['KEYCLOAK_REALM_NAME'],
        #         client_secret_key=self.config['DEFAULT']['KEYCLOAK_CLIENT_SECRET'])
        #     BMcsvfile.users2csv(
        #         list_users=kc.get_users(),
        #         file_path=self.config["EXPORT-LOCAL"]["CSV_FILE_PATH"],
        #         separator=self.config["EXPORT-LOCAL"]["CSV_FILE_SP"])
        # except (exceptions.KeycloakGetError, exceptions.KeycloakConnectionError):
        #     logger.error('Unable export users')
        #     parser.print_help()
        #     sys.exit(1)

    def purge(self):
        """Purage keycloak
        """
        parser = argparse.ArgumentParser(
            description="Purage users on keycloak")
        KCtool.__setdefault__(parser)
        args = parser.parse_args(sys.argv[2:])
        self.__parsedefault__(args)
        with open(CONFIG, "w") as configfile:
            self.config.write(configfile)
        self.config.read(CONFIG)
        try:
            kc = Keycloak(
                server_url=self.config['DEFAULT']['KEYCLOAK_SERVER_URL'],
                client_id=self.config['DEFAULT']['KEYCLOAK_CLIENT_ID'],
                realm_name=self.config['DEFAULT']['KEYCLOAK_REALM_NAME'],
                client_secret_key=self.config['DEFAULT']['KEYCLOAK_CLIENT_SECRET'])
            kc.delete_users()
        except (exceptions.KeycloakGetError, exceptions.KeycloakConnectionError):
            logger.error('Unable Purge users')
            parser.print_help()
            sys.exit(1)


def main():
    KCtool()
