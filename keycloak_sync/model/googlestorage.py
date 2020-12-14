import logging
from pathlib import Path, PurePath

import coloredlogs
from google.api_core.exceptions import NotFound
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import storage
from keycloak_sync.abstract_model.storageprovider import StorageProvider

logger = logging.getLogger(__name__)


class GoogleStorage(StorageProvider):
    @staticmethod
    def set_log_level(level: str):
        """Set log level

        Args:
            level (str): log's level
        """
        coloredlogs.install(level=level, logger=logger)

    @staticmethod
    def download(bucket_name: str, source_file: PurePath, destination_file: Path):
        """Download file from bucket

        Args:
            bucket_name (str): bucket name
            source_file (PurePath): source file path
            destination_file (Path): destination path

        Raises:
            GoogleStorage.StorageProviderERROR: Exception raised for errors in the StorageProvider
        """
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(str(source_file))
            blob.download_to_filename(str(destination_file))
            logger.info(f"Download {str(destination_file)}")
        except (DefaultCredentialsError, NotFound) as error:
            raise GoogleStorage.StorageProviderERROR(error)
