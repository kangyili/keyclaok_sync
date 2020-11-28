"""
A command line tool aimed to synchronize and export users on keycloak.
"""
import argparse
import configparser
import os
import sys

from keycloak import exceptions

from keycloak_sync.model.bmcsvfile import BMcsvfile
from keycloak_sync.model.kc import Keycloak
from keycloak_sync.model.log import logging

logger = logging.getLogger(__name__)
CONFIG = f"{os.path.splitext(__name__)[0]}/config.cfg"


class KCtool:
    """Keycloak command line tool
    """

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config["SYNC-LOCAL"] = {}
        self.config["SYNC-BUCKET"] = {}
        self.config["EXPORT-LOCAL"] = {}
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
            dest="KEYCLOAK_SERVER_URL",
            help="Keycloak server url",
        )
        parser.add_argument(
            "--kc-realm",
            default=None,
            dest="KEYCLOAK_REALM_NAME",
            help="Keycloak realm name",
        )
        parser.add_argument(
            "--kc-clt",
            default=None,
            dest="KEYCLOAK_CLIENT_ID",
            help="keycloak client name",
        )
        parser.add_argument(
            "--kc-clt-sct",
            default=None,
            dest="KEYCLOAK_CLIENT_SECRET",
            help="Keycloak cleint secret",
        )

    def __parsedefault__(self, args: object):
        self.config["DEFAULT"][
            "KEYCLOAK_SERVER_URL"
        ] = args.KEYCLOAK_SERVER_URL or os.getenv("KEYCLOAK_SERVER_URL", "None")
        self.config["DEFAULT"][
            "KEYCLOAK_REALM_NAME"
        ] = args.KEYCLOAK_REALM_NAME or os.getenv("KEYCLOAK_REALM_NAME", "None")
        self.config["DEFAULT"][
            "KEYCLOAK_CLIENT_ID"
        ] = args.KEYCLOAK_CLIENT_ID or os.getenv("KEYCLOAK_CLIENT_ID", "None")
        self.config["DEFAULT"][
            "KEYCLOAK_CLIENT_SECRET"
        ] = args.KEYCLOAK_CLIENT_SECRET or os.getenv("KEYCLOAK_CLIENT_SECRET", "None")

    @classmethod
    def __setbucket__(cls, parser: object):
        parser.add_argument(
            "--bk-name",
            default=None,
            dest="BUCKET_NAME",
            help="Cloud Strage Bucket name",
        )
        parser.add_argument(
            "--bk-path",
            default=None,
            dest="BUCKET_PATH",
            help="Cloud Strage Bucket path",
        )

    def __parsebucket__(self, args: object):
        self.config["SYNC-BUCKET"][
            "BUCKET_NAME"
        ] = args.GCS_BUCKET_NAME or os.getenv("BUCKET_NAME", "None")
        self.config["SYNC-BUCKET"][
            "BUCKET_PATH"
        ] = args.GCS_BUCKET_PATH or os.getenv("BUCKET_PATH", "None")

    def sync(self):
        """synchronize users
        """
        parser = argparse.ArgumentParser(
            description="Synchronize users on keycloak")
        KCtool.__setdefault__(parser)
        parser.add_argument(
            "-f", "--file", default=None, dest="CSV_FILE", help="Csv file path"
        )
        parser.add_argument(
            "--sp", default=None, dest="CSV_FILE_SP", help="Csv file sparator"
        )
        parser.add_argument(
            "--header", default=None, dest="CSV_FILE_HEADER", help="Csv file header"
        )
        args = parser.parse_args(sys.argv[2:])
        self.__parsedefault__(args)
        self.config["SYNC-LOCAL"]["CSV_FILE"] = args.CSV_FILE or os.getenv(
            "CSV_FILE", "None"
        )
        self.config["SYNC-LOCAL"]["CSV_FILE_SP"] = args.CSV_FILE_SP or os.getenv(
            "CSV_FILE_SP", ";"
        )
        self.config["SYNC-LOCAL"]["CSV_FILE_HEADER"] = args.CSV_FILE_HEADER or os.getenv(
            "CSV_FILE_HEADER", '0'
        )
        with open(CONFIG, "w") as configfile:
            self.config.write(configfile)
        self.config.read(CONFIG)
        try:
            bmcsvfile = BMcsvfile(
                filepath=self.config['SYNC-LOCAL']['CSV_FILE'],
                separator=self.config["SYNC-LOCAL"]["CSV_FILE_SP"],
                header=self.config["SYNC-LOCAL"]["CSV_FILE_HEADER"])
            kc = Keycloak(server_url=self.config['DEFAULT']['KEYCLOAK_SERVER_URL'],
                          client_id=self.config['DEFAULT']['KEYCLOAK_CLIENT_ID'],
                          realm_name=self.config['DEFAULT']['KEYCLOAK_REALM_NAME'],
                          client_secret_key=self.config['DEFAULT']['KEYCLOAK_CLIENT_SECRET'])
            if bmcsvfile.isformat():
                list_users = bmcsvfile.readcsv2users()
                kc.add_users(users=list_users)
            else:
                logger.error('Invalid CSV file')
                sys.exit(1)
        except (exceptions.KeycloakGetError, exceptions.KeycloakConnectionError, FileNotFoundError):
            logger.error('Unable Synchronize')
            parser.print_help()
            sys.exit(1)

    def syncbk(self):
        """synchronize users from buckets
        """
        parser = argparse.ArgumentParser(
            description="Synchronize users on keycloak from Google Storage Bucket"
        )
        KCtool.__setdefault__(parser)
        KCtool.__setbucket__(parser)
        parser.add_argument(
            "-f", "--file", default=None, dest="CSV_FILE", help="Csv file name"
        )
        args = parser.parse_args(sys.argv[2:])
        self.__parsedefault__(args)
        self.__parsebucket__(args)
        self.config["SYNC-BUCKET"]["CSV_FILE"] = args.CSV_FILE or os.getenv(
            "CSV_FILE", "None"
        )
        with open(CONFIG, "w") as configfile:
            self.config.write(configfile)

    def export(self):
        """export users from keycloak
        """
        parser = argparse.ArgumentParser(
            description="Export users from keycloak")
        KCtool.__setdefault__(parser)
        parser.add_argument(
            "-d", "--dest", default=None, dest="CSV_FILE_PATH", help="Csv file path"
        )
        parser.add_argument(
            "--sp", default=None, dest="CSV_FILE_SP", help="Csv file sparator"
        )
        args = parser.parse_args(sys.argv[2:])
        self.__parsedefault__(args)
        self.config["EXPORT-LOCAL"]["CSV_FILE_PATH"] = args.CSV_FILE_PATH or os.getenv(
            "CSV_FILE_PATH", "./output.csv"
        )
        self.config["EXPORT-LOCAL"]["CSV_FILE_SP"] = args.CSV_FILE_SP or os.getenv(
            "CSV_FILE_SP", ";"
        )

        with open(CONFIG, "w") as configfile:
            self.config.write(configfile)
        self.config.read(CONFIG)

        try:
            kc = Keycloak(server_url=self.config['DEFAULT']['KEYCLOAK_SERVER_URL'],
                          client_id=self.config['DEFAULT']['KEYCLOAK_CLIENT_ID'],
                          realm_name=self.config['DEFAULT']['KEYCLOAK_REALM_NAME'],
                          client_secret_key=self.config['DEFAULT']['KEYCLOAK_CLIENT_SECRET'])
            BMcsvfile.users2csv(list_users=kc.get_users(),
                                file_path=self.config["EXPORT-LOCAL"]["CSV_FILE_PATH"],
                                separator=self.config["EXPORT-LOCAL"]["CSV_FILE_SP"])
        except (exceptions.KeycloakGetError, exceptions.KeycloakConnectionError):
            logger.error('Unable export users')
            parser.print_help()
            sys.exit(1)

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
            kc = Keycloak(server_url=self.config['DEFAULT']['KEYCLOAK_SERVER_URL'],
                          client_id=self.config['DEFAULT']['KEYCLOAK_CLIENT_ID'],
                          realm_name=self.config['DEFAULT']['KEYCLOAK_REALM_NAME'],
                          client_secret_key=self.config['DEFAULT']['KEYCLOAK_CLIENT_SECRET'])
            kc.delete_users()
        except (exceptions.KeycloakGetError, exceptions.KeycloakConnectionError):
            logger.error('Unable Purge users')
            parser.print_help()
            sys.exit(1)
