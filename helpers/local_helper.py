from os import listdir, remove
from os.path import isfile, join
from helpers import api_helper


def get_local_directory_files(path):
    return [f for f in listdir(path) if isfile(join(path, f))]


def delete_file(path, filename):
    api_helper.lock_print(f'Deleting file {filename}...')
    remove(path)
    api_helper.print_success(f'Deleted file {filename}')
