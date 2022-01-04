import os
import shutil
from os import listdir, remove
from os.path import isfile, join, isdir, exists, getsize

from helpers import message_helper
from helpers.models import LocalFile, DriveFile
from helpers.validation_helper import is_valid_name, INVALID_CHARACTERS


def delete_folder(local_folder: LocalFile) -> None:
    if exists(local_folder.absolute_local_path):
        shutil.rmtree(local_folder.absolute_local_path)


def create_folder(root_folder: LocalFile, name: str) -> None:
    if not is_valid_name(name):
        raise Exception(f'Invalid local folder name {name}. Invalid characters {INVALID_CHARACTERS}')

    path = join(root_folder.absolute_local_path, name)
    if not exists(path):
        os.mkdir(path)


def create_local_folders_from_drive(root_folder: LocalFile, folders_to_create: set[DriveFile]) -> None:
    for drive_folder in folders_to_create:
        drive_folder: DriveFile
        local_path = join(root_folder.absolute_local_path, drive_folder.name)
        if (drive_folder.parent.absolute_drive_path == root_folder.absolute_drive_path
                and not exists(local_path)):
            print(f'\nCreating local folder {local_path}...')
            create_folder(root_folder, drive_folder.name)
            message_helper.print_success(f'CREATED local folder {local_path}')

    for file_name in os.listdir(root_folder.absolute_local_path):
        file_path = join(root_folder.absolute_local_path, file_name)
        if isdir(file_path):
            local_folder: LocalFile = LocalFile(absolute_local_path=file_path,
                                                parent=root_folder)
            create_local_folders_from_drive(local_folder, folders_to_create)


def get_folder_files(root_folder: LocalFile) -> set[LocalFile]:
    res = set()

    for file_name in listdir(root_folder.absolute_local_path):
        file_path = join(root_folder.absolute_local_path, file_name)
        if isfile(file_path):
            size = getsize(file_path)
            file = LocalFile(file_path, root_folder, size=size)
            res.add(file)

    return res


def delete_file(local_file: LocalFile) -> None:
    remove(local_file.absolute_local_path)


def get_local_folders(root_folder: LocalFile, parent: LocalFile = None) -> set[LocalFile]:
    nested_folders = set()
    for file_name in os.listdir(root_folder.absolute_local_path):
        file_path = join(root_folder.absolute_local_path, file_name)
        if isdir(file_path):
            local_folder: LocalFile = LocalFile(absolute_local_path=file_path,
                                                parent=root_folder)
            if local_folder in nested_folders:
                raise Exception(f'Duplicate local folders "{local_folder}"')
            nested_folders.add(local_folder)
            nested_folders.update(get_local_folders(local_folder, root_folder))

    if parent is None:
        if root_folder in nested_folders:
            raise Exception(f'Duplicate local folders "{root_folder}"')
        nested_folders.add(root_folder)

    return nested_folders
