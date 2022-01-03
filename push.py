import time
import traceback

import config
from helpers import api_helper, local_helper, message_helper, set_helper
from helpers.models import DriveFile, LocalFile, UserAccount

if __name__ == '__main__':
    try:
        message_helper.print_warning('\nPUSH')

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

        folders_to_create, folders_to_delete = api_helper.fetch_from_local_to_drive(drive_set=drive_folders, local_set=local_folders)

        if len(folders_to_create) > 0:
            message_helper.print_warning('\nDrive folders to create:')
            message_helper.print_warning(folders_to_create)

        if len(folders_to_delete) > 0:
            message_helper.print_cyan('\nDrive folders to delete:')
            message_helper.print_cyan(folders_to_delete)

        if len(folders_to_create) > 0 or len(folders_to_delete) > 0:
            choice = input('\nWould you like to sync folders above? (y/n) ')

            if choice == 'y':
                for drive_folder in folders_to_delete:
                    drive_folder: DriveFile
                    print(f'\nDeleting drive folder {drive_folder}...')
                    api_helper.delete_file(drive_folder)
                    message_helper.print_warning(f'Deleted drive folder {drive_folder}')

                if len(folders_to_create) > 0:
                    api_helper.create_drive_folders_from_local(drive_root, folders_to_create)

                drive_folders = api_helper.get_drive_folders(drive_root)

                local_folders = local_helper.get_local_folders(local_root)

                folders_to_create, folders_to_delete = api_helper.fetch_from_local_to_drive(drive_folders,
                                                                                            local_folders)

                if len(folders_to_create) > 0:
                    raise Exception(f'Drive folders are not equal. To create: {folders_to_create}')

                if len(folders_to_delete) > 0:
                    raise Exception(f'Drive folders are not equal. To delete: {folders_to_delete}')
            else:
                raise Exception('Folders are not equal, please sync them')

        push_dict = {}

        for local_folder in local_folders:
            absolute_drive_path = local_folder.absolute_drive_path
            drive_folder: DriveFile = set_helper.get_from_set_by_string(drive_folders, absolute_drive_path)
            
            drive_file_set = api_helper.get_folder_files(drive_folder)
            
            local_file_set = local_helper.get_folder_files(local_folder)
            
            upload, delete = api_helper.fetch_from_local_to_drive(
                drive_set=drive_file_set,
                local_set=local_file_set
            )

            if len(upload) > 0 or len(delete) > 0:
                push_dict[drive_folder] = {}
                push_dict[drive_folder][api_helper.UPLOAD_TO_DRIVE_KEY] = upload
                push_dict[drive_folder][api_helper.DELETE_ON_DRIVE_KEY] = delete
        
        if len(push_dict) == 0:
            if api_helper.test_items(drive_root=drive_root,
                                     local_root=local_root):
                message_helper.print_success(f'\nEverything is up to date\n{ local_root.absolute_local_path } -> { drive_root }\n')
                exit()
            else:
                raise Exception('\nFolders are not equal, no push items though\n')

        for drive_folder in push_dict:
            message_helper.print_cyan('=' * 40)
            message_helper.print_success(f'FOLDER: {drive_folder}\n')
            message_helper.print_cyan('Will be uploaded:\n')
            
            for local_file in push_dict[drive_folder][api_helper.UPLOAD_TO_DRIVE_KEY]:
                message_helper.print_cyan(local_file.name)
            
            message_helper.print_cyan('=' * 40)
            
            message_helper.print_warning('\n' + '=' * 40)
            message_helper.print_success(f'FOLDER: {drive_folder}\n')
            message_helper.print_warning('Will be deleted:\n')
            
            for drive_file in push_dict[drive_folder][api_helper.DELETE_ON_DRIVE_KEY]:
                message_helper.print_warning(drive_file.name)
                
            message_helper.print_warning('=' * 40 + '\n')

        choice = input('Are you sure to complete the operation? (y/n) ')
        
        if choice == 'y':
            start = time.time()
            
            processed_number_of_files = 0
            total_number_of_files = api_helper.get_amount_of_files(push_dict)
            
            for drive_folder in push_dict:
                upload = push_dict[drive_folder][api_helper.UPLOAD_TO_DRIVE_KEY]
                delete = push_dict[drive_folder][api_helper.DELETE_ON_DRIVE_KEY]

                for drive_file in delete:
                    drive_file: DriveFile
                    print(f'\nDeleting drive file {drive_file.absolute_drive_path}...')
                    api_helper.delete_file(drive_file)
                    processed_number_of_files += 1
                    message_helper.print_success(f'DELETED drive file {drive_file.absolute_drive_path} [{processed_number_of_files / float(total_number_of_files) * 100 : .2f}% ({processed_number_of_files}/{total_number_of_files}) ]')
                
                for local_file in upload:    
                    local_file: LocalFile
                    print(f'\nUploading local file {local_file} --> {local_file.name}...')

                    new_file: DriveFile = api_helper.upload_file(
                        local_file=local_file,
                        drive_folder=drive_folder
                    )
                    processed_number_of_files += 1
                    message_helper.print_success(
                        f'File {new_file.absolute_drive_path} UPLOADED (id {new_file.id}) [{processed_number_of_files / float(total_number_of_files) * 100 : .2f}% ({processed_number_of_files}/{total_number_of_files}) ]')

            if api_helper.test_items(drive_root=drive_root,
                                     local_root=local_root):
                message_helper.print_success('\nPush was done successfully!!!\n')
            else:
                message_helper.print_fail('Push was not completed :(')
            
            message_helper.print_cyan(f'Operation took {time.time() - start : .2f} seconds\n')
        else:
            message_helper.print_fail('\nPush was declined\n')

    except Exception as ex:
        message_helper.print_fail('\nPush was not completed :(\n')
        message_helper.print_fail(ex)
        traceback.print_exc()
