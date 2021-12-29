from config import *
import config
from helpers import api_helper, local_helper, message_helper
import time
from pprint import pprint
import traceback
from helpers.models import DriveFile, LocalFile


if __name__ == '__main__':
    try:
        message_helper.print_warning('\nPUSH')
        
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
        
        push_dict = {}
        
        is_up_to_date = True
        
        for drive_folder in drive_folders:
            name = drive_folder.absolute_path
            local_folder = local_helper.get_item_by_name(local_folders, name)
            
            drive_file_set = api_helper.get_folder_items(name)
            
            local_file_set = local_helper.get_local_directory_files(local_folder.path)
            
            upload, delete = api_helper.fetch_from_local_to_drive(
                drive_set=drive_file_set,
                local_set=local_file_set
            )

            push_dict[drive_folder] = {}
            push_dict[drive_folder][api_helper.UPLOAD_TO_DRIVE_KEY] = upload
            push_dict[drive_folder][api_helper.DELETE_ON_DRIVE_KEY] = delete
            
            if is_up_to_date and (len(upload) != 0 or len(delete) != 0):
                is_up_to_date = False
        
        if is_up_to_date:
            if api_helper.test_items(drive_directory=DRIVE_DIRECTORY, 
                                     local_directory=LOCAL_DIRECTORY):
                message_helper.print_success(f'\nEverything is up to date\n{ LOCAL_DIRECTORY } -> { DRIVE_DIRECTORY }\n')
            else:
                message_helper.print_fail('\nFolders are not equal, no push items though\n')
            exit()
        
        for drive_folder in push_dict:
            message_helper.print_cyan('=' * 40)
            message_helper.print_success(f'FOLDER: {drive_folder}\n')
            message_helper.print_cyan('Will be uploaded:\n')
            
            for f in push_dict[drive_folder][api_helper.UPLOAD_TO_DRIVE_KEY]:
                message_helper.print_cyan(f)
            
            message_helper.print_cyan('=' * 40)
            
            message_helper.print_warning('\n' + '=' * 40)
            message_helper.print_success(f'FOLDER: {drive_folder}\n')
            message_helper.print_warning('Will be deleted:\n')
            
            for f in push_dict[drive_folder][api_helper.DELETE_ON_DRIVE_KEY]:
                message_helper.print_warning(f)
                
            message_helper.print_warning('=' * 40 + '\n')

        choice = input('Are you sure to complete the operation? (y/n) ')
        
        if choice == 'y':
            start = time.time()
            
            config.CURRENT_LOAD_NUMBER = 0
            config.TOTAL_LOAD_NUMBER = api_helper.get_amount_of_files(push_dict)
            
            for drive_folder in push_dict:
                upload = push_dict[drive_folder][api_helper.UPLOAD_TO_DRIVE_KEY]
                delete = push_dict[drive_folder][api_helper.DELETE_ON_DRIVE_KEY]
                
                for local_file in upload:    
                    local_file: LocalFile
                    
                    api_helper.upload_file(
                        target_name=local_file.name,
                        source_name=local_file.absolute_path,
                        folder=drive_folder
                        
                    )
                    
                for drive_file in delete:
                    drive_file: DriveFile
                    
                    api_helper.delete_file(drive_file)

            if api_helper.test_items(drive_directory=DRIVE_DIRECTORY, 
                                     local_directory=LOCAL_DIRECTORY):
                message_helper.print_success('\nPush was done successfully!!!\n')
            else:
                message_helper.print_fail('Push was not completed :(')
            
            message_helper.print_cyan(f'Operation took {time.time() - start : .2f} seconds\n')
        else:
            message_helper.print_fail('\nPush was declined.\n')

    except Exception as ex:
        message_helper.print_fail('\nPush was not completed :(\n')
        message_helper.print_fail(ex)
        traceback.print_exc()
