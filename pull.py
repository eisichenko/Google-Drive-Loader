from config import *
import config
from helpers import api_helper, local_helper, message_helper
from os.path import join
import time
from pprint import pprint
import traceback
from helpers.models import DriveFile, LocalFile


if __name__ == '__main__':
    try:
        message_helper.print_warning('\nPULL')

        api_helper.print_account_info()

        DRIVE_DIRECTORY = PATH.drive_folder_name
        LOCAL_DIRECTORY = PATH.local_folder_path

        drive_folders = api_helper.get_drive_nested_folders(DRIVE_DIRECTORY)

        print('Drive folders:')
        pprint(drive_folders)

        local_folders = local_helper.get_local_nested_folders(LOCAL_DIRECTORY)

        print('\nLocal folders:')
        pprint(local_folders)

        if local_folders != drive_folders:
            raise Exception(f'Local and drive folders are not equal')

        pull_dict = {}

        is_up_to_date = True

        for drive_folder in drive_folders:
            name = drive_folder.absolute_path
            local_folder = local_helper.get_item_by_name(local_folders, name)

            drive_file_set = api_helper.get_folder_items(name)

            local_file_set = local_helper.get_local_directory_files(local_folder.path)

            download, delete = api_helper.fetch_from_drive_to_local(
                drive_set=drive_file_set,
                local_set=local_file_set

            )
            pull_dict[drive_folder] = {}
            pull_dict[drive_folder][api_helper.DOWNLOAD_FROM_DRIVE_KEY] = download
            pull_dict[drive_folder][api_helper.DELETE_IN_LOCAL_KEY] = delete

            if is_up_to_date and (len(download) != 0 or len(delete) != 0):
                is_up_to_date = False

        if is_up_to_date:
            if api_helper.test_items(
                    drive_directory=DRIVE_DIRECTORY,
                    local_directory=LOCAL_DIRECTORY):
                message_helper.print_success(f'\nEverything is up to date\n{DRIVE_DIRECTORY} -> {LOCAL_DIRECTORY}\n')
            else:
                message_helper.print_fail('\nFolders are not equal, no pull items though\n')
            exit()

        for drive_folder in pull_dict:
            message_helper.print_cyan('=' * 40)
            message_helper.print_success(f'FOLDER: {drive_folder}\n')
            message_helper.print_cyan('Will be downloaded:\n')

            for f in pull_dict[drive_folder][api_helper.DOWNLOAD_FROM_DRIVE_KEY]:
                message_helper.print_cyan(f)

            message_helper.print_cyan('=' * 40)

            message_helper.print_warning('\n' + '=' * 40)
            message_helper.print_success(f'FOLDER: {drive_folder}\n')
            message_helper.print_warning('Will be deleted:\n')

            for f in pull_dict[drive_folder][api_helper.DELETE_IN_LOCAL_KEY]:
                message_helper.print_warning(f)

            message_helper.print_warning('=' * 40 + '\n')

        choice = input('Are you sure to complete the operation? (y/n) ')

        if choice == 'y':
            start = time.time()

            config.CURRENT_LOAD_NUMBER = 0
            config.TOTAL_LOAD_NUMBER = api_helper.get_amount_of_files(pull_dict)

            for drive_folder in pull_dict:
                local_folder = local_helper.get_item_by_name(local_folders, drive_folder.absolute_path)

                download = pull_dict[drive_folder][api_helper.DOWNLOAD_FROM_DRIVE_KEY]
                delete = pull_dict[drive_folder][api_helper.DELETE_IN_LOCAL_KEY]

                for drive_file in download:
                    drive_file: DriveFile

                    api_helper.download_file(
                        file_id=drive_file.id,
                        name=drive_file.name,
                        local_path=join(local_folder.path, drive_file.name)
                    )

                for local_file in delete:
                    local_file: LocalFile

                    local_helper.delete_file(local_file)

            if api_helper.test_items(drive_directory=DRIVE_DIRECTORY,
                                     local_directory=LOCAL_DIRECTORY):
                message_helper.print_success('\nPull was done successfully!!!\n')
            else:
                message_helper.print_fail('Pull was not completed :(')

            message_helper.print_cyan(f'Operation took {time.time() - start : .2f} seconds\n')
        else:
            message_helper.print_fail('\nPull was declined.\n')

    except Exception as ex:
        message_helper.print_fail('\nPull was not completed :(\n')
        message_helper.print_fail(ex)
        traceback.print_exc()
