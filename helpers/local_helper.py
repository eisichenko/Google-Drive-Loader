from os import listdir, remove
from os.path import isfile, join

import helpers.message_helper
from helpers import api_helper
import os
from helpers.models import LocalFile
import config


def get_local_directory_files(path) -> set:
    res = [LocalFile(join(path, f)) for f in listdir(path) if isfile(join(path, f))]
    
    if api_helper.has_duplicates(res):
        raise Exception(f'Duplicate files in local folder {path}')

    return set(res)


def delete_file(local_file: LocalFile):
    remove(local_file.path)
    config.CURRENT_LOAD_NUMBER += 1
    loaded = config.CURRENT_LOAD_NUMBER
    total = config.TOTAL_LOAD_NUMBER
    helpers.message_helper.print_success(f'Deleted file {local_file.name} [{loaded / float(total) * 100 : .2f}% ({loaded}/{total}) ]')
    

def get_local_nested_folders(path) -> set:
    res = [LocalFile(x[0]) for x in os.walk(path)]
    if api_helper.has_duplicates(res):
        raise Exception(f'Local folder {path} has duplicate folders {api_helper.get_duplicates(res)}')
    return set(res)


def get_item_by_name(items, name):
    for item in items:
        item: LocalFile
        if item.name == name:
            return item
    
    raise Exception(f'Local item {name} not found')