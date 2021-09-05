from __future__ import print_function
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
from config import *
import config
from helpers import api_helper, local_helper
from os.path import join
import time
import threading

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
        for path in PATHS:
            DRIVE_DIRECTORY = path.drive_folder_name
            LOCAL_DIRECTORY = path.local_folder_path
            
            drive_items = api_helper.get_folder_items(DRIVE_DIRECTORY)
            
            drive_items_names = list(map(lambda x : x['name'], drive_items))
            
            drive_names_set = set(drive_items_names)
            
            if len(drive_items_names) != len(drive_names_set):
                raise Exception('Duplicate drive items')
            
            local_items_names = local_helper.get_local_directory_files(LOCAL_DIRECTORY)
            
            local_names_set = set(local_items_names)
            
            if len(local_items_names) != len(local_names_set):
                raise Exception('Duplicate local items')
            
            upload, delete = api_helper.fetch_from_local_to_drive(drive_names_set=drive_names_set,
                                                local_names_set=local_names_set)
            
            if len(upload) == 0 and len(delete) == 0:
                if api_helper.test_items(drive_directory=DRIVE_DIRECTORY, 
                                                local_directory=LOCAL_DIRECTORY):
                    api_helper.print_success(f'\nEverything is up to date\n{ LOCAL_DIRECTORY } : { DRIVE_DIRECTORY }')
                else:
                    api_helper.print_fail('\nSomething went wrong\n')
                continue
            
            api_helper.print_cyan('=' * 40)
            
            api_helper.print_cyan('Will be uploaded:\n')
            
            for f in upload:
                api_helper.print_cyan(f)
            
            api_helper.print_cyan('=' * 40)
            
            api_helper.print_warning('\n' + '=' * 40)
            
            api_helper.print_warning('Will be deleted:\n')
            
            for f in delete:
                api_helper.print_warning(f)
                
            api_helper.print_warning('=' * 40 + '\n')

            choice = input('Are you sure to complete the operation? (y/n) ')
            
            if choice == 'y':
                start = time.time()
                
                threads = []
                
                config.CURRENT_LOAD_NUMBER = 0
                config.TOTAL_LOAD_NUMBER = len(upload)
                
                for name in upload:
                    threads.append(threading.Thread(target=api_helper.upload_file,
                                                    kwargs={'target_name': name,
                                                            'source_name': join(LOCAL_DIRECTORY, name), 
                                                            'folder_name': DRIVE_DIRECTORY}))
                    
                for name in delete:
                    item = api_helper.get_item_by_name(files=drive_items, name=name)
                    threads.append(threading.Thread(target=api_helper.delete_file,
                                                    kwargs={'file_id': item['id'],
                                                            'filename': item['name']}))

                for thread in threads:
                    thread.start()
                    
                for thread in threads:
                    thread.join()

                api_helper.print_cyan(f'\nOperation took {time.time() - start : .2f} seconds')
                
                if api_helper.test_items(drive_directory=DRIVE_DIRECTORY, 
                                                local_directory=LOCAL_DIRECTORY) and EXECUTION_RESULT:
                    api_helper.print_success('\nPush was done successfully!!!\n')
                else:
                    api_helper.print_fail('Push was not completed :(')
            else:
                api_helper.print_fail('\nPush declined.\n')

    except Exception as ex:
        api_helper.print_fail(ex)
        api_helper.print_fail('Push was not completed :(')
