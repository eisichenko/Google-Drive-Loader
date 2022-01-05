import os.path
from pathlib import Path
from typing import Union

from helpers.validation_helper import is_valid_name, INVALID_CHARACTERS


class AbstractFile:
    def __init__(self, name: str, parent: 'AbstractFile', size: int = 0):
        self.child_folders: set[Union['AbstractFile', 'DriveFile', 'LocalFile']] = set()
        self.child_files: set[Union['AbstractFile', 'DriveFile', 'LocalFile']] = set()
        self.parent = parent
        self.name = name
        self.size = int(size)

        if parent is None:
            self.absolute_drive_path = name
        else:
            self.absolute_drive_path = os.path.join(parent.absolute_drive_path, name)

        if not is_valid_name(name):
            raise Exception(f'Invalid name {name} [ {self.absolute_drive_path} ]. Invalid characters {INVALID_CHARACTERS}')

    def __eq__(self, other):
        if not isinstance(other, AbstractFile):
            return False

        if other is None:
            return self.absolute_drive_path is None

        other: AbstractFile

        return self.absolute_drive_path == other.absolute_drive_path

    def __hash__(self):
        return self.absolute_drive_path.__hash__()

    def __str__(self):
        return self.absolute_drive_path

    def __repr__(self):
        return self.absolute_drive_path


class DriveFile(AbstractFile):
    def __init__(self, file_id: str, name: str, parent: Union['DriveFile', None], size: int = 0):
        super().__init__(name, parent, size)
        self.id = file_id


class LocalFile(AbstractFile):
    def __init__(self, absolute_local_path: str, parent: Union['LocalFile', None], size: int = 0):
        super().__init__(Path(absolute_local_path).name, parent, size)
        self.absolute_local_path = absolute_local_path


class UserAccount:
    def __init__(self, email: str, display_name: str):
        self.email = email
        self.display_name = display_name
