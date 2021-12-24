from __future__ import print_function
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from config import *
import config
from helpers import api_helper, local_helper
from os.path import join
import time
from pprint import pprint
import traceback

from helpers.files import DriveFile, LocalFile


EXECUTION_RESULT = True

SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_id.json', SCOPES)
    creds = tools.run_flow(flow, store)
DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))


if __name__ == '__main__':
    try:
        api_helper.print_warning('\nPUSH')
        
        about = DRIVE.about().get(fields='user').execute()
        
        api_helper.print_warning(f'\nCurrent account: {about["user"]["emailAddress"]}')
        api_helper.print_warning(f'Account name: {about["user"]["displayName"]}')
        
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
            name = drive_folder.name
            local_folder = local_helper.get_item_by_name(local_folders, name)
            
            drive_file_set = api_helper.get_folder_items(name)
            
            local_file_set = local_helper.get_local_directory_files(local_folder.path)
            
            upload, delete = api_helper.fetch_from_local_to_drive(drive_set=drive_file_set,
                                                local_set=local_file_set)
            push_dict[drive_folder] = {}
            push_dict[drive_folder][api_helper.UPLOAD_TO_DRIVE_KEY] = upload
            push_dict[drive_folder][api_helper.DELETE_ON_DRIVE_KEY] = delete
            
            if is_up_to_date and (len(upload) != 0 or len(delete) != 0):
                is_up_to_date = False
        
        if is_up_to_date:
            if api_helper.test_items(drive_directory=DRIVE_DIRECTORY, 
                                            local_directory=LOCAL_DIRECTORY):
                api_helper.print_success(f'\nEverything is up to date\n{ LOCAL_DIRECTORY } -> { DRIVE_DIRECTORY }\n')
            else:
                api_helper.print_fail('\nFolders are not equal, no push items though\n')
            exit()
        
        for drive_folder in push_dict:
            api_helper.print_cyan('=' * 40)
            api_helper.print_success(f'FOLDER: {drive_folder}\n')
            api_helper.print_cyan('Will be uploaded:\n')
            
            for f in push_dict[drive_folder][api_helper.UPLOAD_TO_DRIVE_KEY]:
                api_helper.print_cyan(f)
            
            api_helper.print_cyan('=' * 40)
            
            api_helper.print_warning('\n' + '=' * 40)
            api_helper.print_success(f'FOLDER: {drive_folder}\n')
            api_helper.print_warning('Will be deleted:\n')
            
            for f in push_dict[drive_folder][api_helper.DELETE_ON_DRIVE_KEY]:
                api_helper.print_warning(f)
                
            api_helper.print_warning('=' * 40 + '\n')

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
                        source_name=local_file.path,
                        folder=drive_folder
                        
                    )
                    
                for drive_file in delete:
                    drive_file: DriveFile
                    
                    api_helper.delete_file(drive_file)

            if api_helper.test_items(drive_directory=DRIVE_DIRECTORY, 
                                            local_directory=LOCAL_DIRECTORY) and EXECUTION_RESULT:
                api_helper.print_success('\nPush was done successfully!!!\n')
            else:
                api_helper.print_fail('Push was not completed :(')
            
            api_helper.print_cyan(f'Operation took {time.time() - start : .2f} seconds\n')
        else:
            api_helper.print_fail('\nPush was declined.\n')

    except Exception as ex:
        api_helper.print_fail(ex)
        api_helper.print_fail('Push was not completed :(')
        traceback.print_exc()
