import yaml
from typing import Optional
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFileList, GoogleDriveFile
from module.debug import log_error


class DriveUtils:
    def __init__(self):
        self._gdrive = None
        with open('config/settings.yaml', 'r', encoding='utf-8') as yaml_config:
            self.config_map = yaml.load(yaml_config, Loader=yaml.SafeLoader)

    @property
    def gdrive(self) -> GoogleDrive:
        'Returns the active drive.GoogleDrive instance.'
        if self._gdrive is None:
            # gauth uses all the client_config of settings.yaml
            gauth = GoogleAuth(settings_file="./config/settings.yaml")
            gauth.CommandLineAuth()
            self._gdrive = GoogleDrive(gauth)
        return self._gdrive

    def list_files(self, folder_id: Optional[str] = None) -> Optional[GoogleDriveFileList]:
        'Returns a list of files or folders in the given directory'
        folder_id = folder_id or self.config_map['drive_folder_id']
        try:
            return self.gdrive.ListFile({
                'q': f"'{folder_id}' in parents and trashed=false",
                'orderBy': 'folder,title',
            }).GetList()
        # pylint: disable=broad-except
        except Exception as e:
            log_error(header="drive_handler", error=e)
            return None

    def get_file(self, file_id: str) -> GoogleDriveFile:
        'Shorthand for self.gdrive.CreateFile'
        return self.gdrive.CreateFile({'id': file_id})


drive_utils = DriveUtils()
