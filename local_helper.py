from os import listdir
from os.path import isfile, join


def get_local_directory_files(path):
    return [f for f in listdir(path) if isfile(join(path, f))]
