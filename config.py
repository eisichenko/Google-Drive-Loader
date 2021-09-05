import os


class Path:
    def __init__(self, local_folder_path, drive_folder_name):
        self.local_folder_path = local_folder_path
        self.drive_folder_name = drive_folder_name


PAGESIZE = 1000
LOADING_LIMIT = 10

CURRENT_LOAD_NUMBER = 0
TOTAL_LOAD_NUMBER = 0

PATHS = []

if os.name == 'nt':
    PATHS.append(Path('D:\\audios\\Happy', 'Happy'))
    PATHS.append(Path('D:\\audios\\Sad', 'Sad'))
else:
    PATHS.append(Path('/media/data/audios/Happy', 'Happy'))
    PATHS.append(Path('/media/data/audios/Sad', 'Sad'))
