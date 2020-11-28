from abc import ABC, abstractmethod
from pathlib import Path, PurePath


class Storage(ABC):
    def __init__(self, kind: str, bucket_name: str, url_prefix: str):
        """An abstract class to represent Cloud Storage infrastructures
        and implement basic upload / download functions in order to
        avoid a direct adherence of the code to a certain cloud provider.

        Args:
            kind (str): The name of the cloud storage service.
            bucket_name (str): The bucket name.
            url_prefix (str): The url prefix (like ``gs://`` or ``s3://``)
        """
        self.kind = kind
        self.bucket_name = bucket_name
        self.url_prefix = url_prefix

    @abstractmethod
    def upload(self, local_path: Path, cloud_path: PurePath):
        """An abstract function for uploading a file.

        Args:
            local_path (Path): the local path of the file to upload.
            cloud_path (PurePath): the relative cloud path where to upload\
            the file to.
        """
        raise NotImplementedError

    @abstractmethod
    def download(self, cloud_path: PurePath, local_path: Path):
        """An abstract function for downloading a file.

        Args:
            cloud_path (PurePath): the relative cloud path where the file\
            to download is.
            local_path (Path): the local path where to download the file to.

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError
