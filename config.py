import os


class Path:
    def __init__(self, local_folder_path, drive_folder_name):
        self.local_folder_path = local_folder_path
        self.drive_folder_name = drive_folder_name


PAGESIZE = 1000

CURRENT_LOAD_NUMBER = 0
TOTAL_LOAD_NUMBER = 0


if os.name == 'nt':
    PATH = Path('D:\\audios', 'audios')
else:
    PATH = Path('/media/data/audios', 'audios')
