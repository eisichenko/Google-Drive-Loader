from typing import Union

from helpers.models import AbstractFile, DriveFile, LocalFile


def get_from_set_by_string(s: set[Union[AbstractFile, DriveFile, LocalFile]], name: str) -> Union[AbstractFile, DriveFile, LocalFile]:
    for item in s:
        item: AbstractFile
        if item.absolute_drive_path == name:
            return item

    raise Exception(f'Local item {name} not found')


def get_amount_of_files(folders: dict[AbstractFile, dict[str, set[AbstractFile]]]) -> int:
    return sum(len(folders[folder][files_key])
               for folder in folders
               for files_key in folders[folder])


def get_size_of_file_set(files: set[Union[AbstractFile, DriveFile, LocalFile]]) -> int:
    return sum(file.size for file in files)


def get_total_size_to_process(folders: dict[AbstractFile, dict[str, set[AbstractFile]]]) -> int:
    return sum(get_size_of_file_set(folders[folder][files_key])
               for folder in folders
               for files_key in folders[folder])
