import os
import pathlib

PROJECT_ROOT_ABS_PATH = os.path.dirname(os.path.abspath(__file__))
PAGESIZE = 1000

if os.name == 'nt':
    LOCAL_ROOT_PATH = 'D:\\audios'
else:
    LOCAL_ROOT_PATH = '/media/data/audios'

# drive folder name and local folder name will be the same
DRIVE_ROOT_NAME = pathlib.Path(LOCAL_ROOT_PATH).name
