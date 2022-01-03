import os
import pathlib


PAGESIZE = 1000

if os.name == 'nt':
    LOCAL_ROOT_PATH = 'D:\\audios'
else:
    # LOCAL_ROOT_PATH = '/media/data/audios'
    LOCAL_ROOT_PATH = "/media/data/programming/SomePrograms/Python/Google-Drive-Loader/files'"
    # LOCAL_ROOT_PATH = "/media/data/programming/SomePrograms/Python/Google-Drive-Loader/test"

# drive folder name and local folder name will be the same
DRIVE_ROOT_NAME = pathlib.Path(LOCAL_ROOT_PATH).name
