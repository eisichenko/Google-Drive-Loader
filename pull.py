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
        api_helper.print_warning('\nPULL')
        
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
            name = drive_folder.name
            local_folder = local_helper.get_item_by_name(local_folders, name)
            
            drive_file_set = api_helper.get_folder_items(name)
            
            local_file_set = local_helper.get_local_directory_files(local_folder.path)
            
            download, delete = api_helper.fetch_from_drive_to_local(drive_set=drive_file_set,
                                                local_set=local_file_set)
            pull_dict[drive_folder] = {}
            pull_dict[drive_folder][api_helper.DOWNLOAD_FROM_DRIVE_KEY] = download
            pull_dict[drive_folder][api_helper.DELETE_IN_LOCAL_KEY] = delete
            
            if is_up_to_date and (len(download) != 0 or len(delete) != 0):
                is_up_to_date = False
        
        if is_up_to_date:
            if api_helper.test_items(drive_directory=DRIVE_DIRECTORY, 
                                            local_directory=LOCAL_DIRECTORY):
                api_helper.print_success(f'\nEverything is up to date\n{ DRIVE_DIRECTORY } -> { LOCAL_DIRECTORY }\n')
            else:
                api_helper.print_fail('\nFolders are not equal, no pull items though\n')
            exit()
        
        for drive_folder in pull_dict:
            api_helper.print_cyan('=' * 40)
            api_helper.print_success(f'FOLDER: {drive_folder}\n')
            api_helper.print_cyan('Will be downloaded:\n')
            
            for f in pull_dict[drive_folder][api_helper.DOWNLOAD_FROM_DRIVE_KEY]:
                api_helper.print_cyan(f)
            
            api_helper.print_cyan('=' * 40)
            
            api_helper.print_warning('\n' + '=' * 40)
            api_helper.print_success(f'FOLDER: {drive_folder}\n')
            api_helper.print_warning('Will be deleted:\n')
            
            for f in pull_dict[drive_folder][api_helper.DELETE_IN_LOCAL_KEY]:
                api_helper.print_warning(f)
                
            api_helper.print_warning('=' * 40 + '\n')

        choice = input('Are you sure to complete the operation? (y/n) ')
        
        if choice == 'y':
            start = time.time()
            
            config.CURRENT_LOAD_NUMBER = 0
            config.TOTAL_LOAD_NUMBER = api_helper.get_amount_of_files(pull_dict)
            
            for drive_folder in pull_dict:
                local_folder = local_helper.get_item_by_name(local_folders, drive_folder.name)
                
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
                                            local_directory=LOCAL_DIRECTORY) and EXECUTION_RESULT:
                api_helper.print_success('\nPull was done successfully!!!\n')
            else:
                api_helper.print_fail('Pull was not completed :(')
            
            api_helper.print_cyan(f'Operation took {time.time() - start : .2f} seconds\n')
        else:
            api_helper.print_fail('\nPull was declined.\n')

    except Exception as ex:
        api_helper.print_fail(ex)
        api_helper.print_fail('Pull was not completed :(')
        # traceback.print_exc()
