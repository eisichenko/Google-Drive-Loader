import time
import traceback

import config
from helpers import api_helper, local_helper, message_helper, set_helper
from helpers.models import DriveFile, LocalFile, UserAccount

if __name__ == '__main__':
    try:
        message_helper.print_warning('\nPULL')

        user_account: UserAccount = api_helper.get_account_info()

        message_helper.print_warning(f'\nCurrent account: {user_account.email}')
        message_helper.print_warning(f'Account name: {user_account.display_name}')

        drive_root: DriveFile = api_helper.get_file_by_name(config.DRIVE_ROOT_NAME, is_folder=True)
        local_root: LocalFile = LocalFile(config.LOCAL_ROOT_PATH, parent=None)

        drive_folders = api_helper.get_drive_folders(drive_root)

        print('All drive folders:')
        print(drive_folders)

        local_folders = local_helper.get_local_folders(local_root)

        print('\nAll local folders:')
        print(local_folders)

        folders_to_create, folders_to_delete = api_helper.fetch_from_drive_to_local(drive_folders,
                                                                                    local_folders)

        if len(folders_to_create) > 0:
            message_helper.print_warning('\nLocal folders to create:')
            message_helper.print_warning(folders_to_create)

        if len(folders_to_delete) > 0:
            message_helper.print_cyan('\nLocal folders to delete:')
            message_helper.print_cyan(folders_to_delete)

        if len(folders_to_create) > 0 or len(folders_to_delete) > 0:
            choice = input('\nWould you like to sync folders above? (y/n) ')

            if choice == 'y':
                for local_folder in folders_to_delete:
                    local_folder: LocalFile
                    local_helper.delete_folder(local_folder)
                    message_helper.print_warning(f'\nDeleted local folder {local_folder}')

                if len(folders_to_create) > 0:
                    local_helper.create_local_folders_from_drive(local_root, folders_to_create)

                drive_folders = api_helper.get_drive_folders(drive_root)

                local_folders = local_helper.get_local_folders(local_root)

                folders_to_create, folders_to_delete = api_helper.fetch_from_drive_to_local(drive_folders,
                                                                                            local_folders)

                if len(folders_to_create) > 0:
                    raise Exception(f'Local folders are not equal. To create: {folders_to_create}')

                if len(folders_to_delete) > 0:
                    raise Exception(f'Local folders are not equal. To delete: {folders_to_delete}')
            else:
                raise Exception('Folders are not equal, please sync them')

        pull_dict = {}

        for drive_folder in drive_folders:
            absolute_drive_path = drive_folder.absolute_drive_path
            local_folder: LocalFile = set_helper.get_from_set_by_string(local_folders, absolute_drive_path)

            drive_file_set = api_helper.get_folder_files(drive_folder)

            local_file_set = local_helper.get_folder_files(local_folder)

            download, delete = api_helper.fetch_from_drive_to_local(
                drive_set=drive_file_set,
                local_set=local_file_set
            )

            if len(download) > 0 or len(delete) > 0:
                pull_dict[drive_folder] = {}
                pull_dict[drive_folder][api_helper.DOWNLOAD_FROM_DRIVE_KEY] = download
                pull_dict[drive_folder][api_helper.DELETE_IN_LOCAL_KEY] = delete

        if len(pull_dict) == 0:
            if api_helper.test_items(drive_root=drive_root, local_root=local_root):
                message_helper.print_success(f'\nEverything is up to date\n{drive_root} -> {local_root.absolute_local_path}\n')
                exit()
            else:
                raise Exception('\nFolders are not equal, no push items though\n')

        for drive_folder in pull_dict:
            message_helper.print_cyan('=' * 40)
            message_helper.print_success(f'FOLDER: {drive_folder}\n')
            message_helper.print_cyan('Will be downloaded:\n')

            for drive_file in pull_dict[drive_folder][api_helper.DOWNLOAD_FROM_DRIVE_KEY]:
                drive_file: DriveFile
                message_helper.print_cyan(drive_file.name)

            message_helper.print_cyan('=' * 40)

            message_helper.print_warning('\n' + '=' * 40)
            message_helper.print_success(f'FOLDER: {drive_folder}\n')
            message_helper.print_warning('Will be deleted:\n')

            for local_file in pull_dict[drive_folder][api_helper.DELETE_IN_LOCAL_KEY]:
                message_helper.print_warning(local_file.name)

            message_helper.print_warning('=' * 40 + '\n')

        choice = input('Are you sure to complete the operation? (y/n) ')

        if choice == 'y':
            start = time.time()

            processed_number_of_files = 0
            total_number_of_files = api_helper.get_amount_of_files(pull_dict)

            for drive_folder in pull_dict:
                local_folder = set_helper.get_from_set_by_string(local_folders, drive_folder.absolute_drive_path)

                download = pull_dict[drive_folder][api_helper.DOWNLOAD_FROM_DRIVE_KEY]
                delete = pull_dict[drive_folder][api_helper.DELETE_IN_LOCAL_KEY]

                for local_file in delete:
                    local_file: LocalFile
                    local_helper.delete_file(local_file)
                    processed_number_of_files += 1
                    message_helper.print_success(f'\nDELETED local file {local_file.absolute_drive_path} [{processed_number_of_files / float(total_number_of_files) * 100 : .2f}% ({processed_number_of_files}/{total_number_of_files}) ]')

                for drive_file in download:
                    drive_file: DriveFile

                    print(f'\nDownloading drive file {drive_file.name}...')
                    api_helper.download_file(
                        drive_file=drive_file,
                        local_folder=local_folder
                    )
                    processed_number_of_files += 1
                    message_helper.print_success(f'DOWNLOADED drive file {drive_file.absolute_drive_path} [{processed_number_of_files / float(total_number_of_files) * 100 : .2f}% ({processed_number_of_files}/{total_number_of_files}) ]')

            if api_helper.test_items(drive_root=drive_root,
                                     local_root=local_root):
                message_helper.print_success('\nPull was done successfully!!!\n')
            else:
                message_helper.print_fail('Pull was not completed :(')

            message_helper.print_cyan(f'Operation took {time.time() - start : .2f} seconds\n')
        else:
            message_helper.print_fail('\nPull was declined\n')

    except Exception as ex:
        message_helper.print_fail('\nPull was not completed :(\n')
        message_helper.print_fail(ex)
        traceback.print_exc()
