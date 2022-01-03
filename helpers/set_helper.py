from helpers.models import AbstractFile


def get_from_set_by_string(s: set[AbstractFile], name: str):
    for item in s:
        item: AbstractFile
        if item.absolute_drive_path == name:
            return item

    raise Exception(f'Local item {name} not found')
