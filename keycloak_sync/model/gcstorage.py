import os
from pathlib import Path, PurePath

from google.cloud import storage as gcs

from keycloak_sync.abstract.cloud_storage import Storage


class GoogleCloudStorage(Storage):

    GCS = "GCS"
    GCS_PREFIX = "gs://"

    def __init__(self, bucket_name: str):
        """Test

        Args:
            bucket_name (str): The cloud storage bucket name.
        """
        super().__init__(
            GoogleCloudStorage.GCS,
            bucket_name=bucket_name,
            url_prefix=GoogleCloudStorage.GCS_PREFIX,
        )
        self.client = gcs.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def upload(self, local_path: Path, cloud_path: PurePath):
        blob = self.bucket.blob(str(cloud_path))
        blob.upload_from_filename(str(local_path))

    def download(self, cloud_path: PurePath, local_path: Path):
        blob = self.bucket.get_blob(str(cloud_path))
        blob.download_to_filename(str(local_path))
