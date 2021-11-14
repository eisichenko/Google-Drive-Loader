from helpers.files import *
from push import creds, EXECUTION_RESULT
from googleapiclient import discovery
from httplib2 import Http
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from config import *
import config
import io
from helpers import local_helper
import collections
import traceback


DRIVE_FOLDER_TYPE = 'application/vnd.google-apps.folder'

UPLOAD_TO_DRIVE_KEY = 'upload_to_drive'
DELETE_ON_DRIVE_KEY = 'delete_on_drive'
DOWNLOAD_FROM_DRIVE_KEY = 'download_from_drive'
DELETE_IN_LOCAL_KEY = 'delete_in_local'


class bcolors:
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_success(string):
    print(bcolors.GREEN + bcolors.BOLD + str(string) + bcolors.ENDC)


def print_fail(string):
    print(bcolors.FAIL + bcolors.BOLD + str(string) + bcolors.ENDC)


def print_cyan(string):
    print(bcolors.CYAN + bcolors.BOLD + str(string) + bcolors.ENDC)


def print_warning(string):
    print(bcolors.WARNING + bcolors.BOLD + str(string) + bcolors.ENDC)


def get_all_files():
    
    print('\nGetting all files...\n')

    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    response = DRIVE.files().list(q='trashed=false', pageSize=PAGESIZE).execute()
    
    files = response.get('files', [])
    nextPageToken = response.get('nextPageToken')

    while nextPageToken:
        response = DRIVE.files().list(q='trashed=false', pageSize=PAGESIZE, pageToken=nextPageToken).execute()
        nextPageToken = response.get('nextPageToken')
        files.extend(response.get('files', []))
    
    return files


def upload_file(target_name, source_name, folder: DriveFile):
    try:
        if folder != None:
            file_metadata = { 'name': target_name,
                            'parents': [folder.id]
                            }
        else:
            file_metadata = { 'name': target_name }
        
        print(f'\nUploading file {source_name} --> {target_name}...\n')
        
        media = MediaFileUpload(source_name,
                                resumable=True)
        
        DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
        file = DRIVE.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        
        if file:
            config.CURRENT_LOAD_NUMBER += 1
            loaded = config.CURRENT_LOAD_NUMBER
            total = config.TOTAL_LOAD_NUMBER
            print_success(f'File {file["name"]} UPLOADED (id {file["id"]}) [{loaded / float(total) * 100 : .2f}% ({loaded}/{total}) ]')
        else:
            raise Exception('Could not upload file')
    except Exception as ex:
        print_fail(f'File {source_name} FAIL UPLOAD')
        print_fail(ex)
        global EXECUTION_RESULT
        EXECUTION_RESULT = False
        traceback.print_exc()
            

def get_folder_items(folder_name) -> set:
    try:
        print(f'\nGetting files from folder {folder_name}...\n')
        
        folder_id = _get_id_by_name(folder_name)
        
        DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
        response = DRIVE.files().list(q=f"'{folder_id}' in parents and mimeType != '{DRIVE_FOLDER_TYPE}' and trashed=false", 
                        pageSize=PAGESIZE).execute()

        files = response['files']
        nextPageToken = response.get('nextPageToken')
        
        while nextPageToken:
            response = DRIVE.files().list(q=f"'{folder_id}' in parents and mimeType != '{DRIVE_FOLDER_TYPE}' and trashed=false", 
                            pageSize=PAGESIZE, pageToken=nextPageToken).execute()
            nextPageToken = response.get('nextPageToken')
            files.extend(response.get('files', []))
            
        drive_files = [DriveFile(file['id'], file['name']) for file in files]
        
        if has_duplicates(drive_files):
            raise Exception(f'Duplicate files in drive folder {folder_name}')
        
        return set(drive_files)

    except Exception as ex:
        print_fail(ex)
        global EXECUTION_RESULT
        EXECUTION_RESULT = False
        traceback.print_exc()
        

def get_drive_nested_folders(folder_name) -> set:
    # all folder names should be unique
    try:
        files = []
        
        print(f'\nGetting nested folders from folder {folder_name}...\n')
        
        folder_id = _get_folder_id_by_name(folder_name)
        
        current_folder = DriveFile(folder_id, folder_name)
            
        DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
        response = DRIVE.files().list(q=f"'{folder_id}' in parents and mimeType = '{DRIVE_FOLDER_TYPE}' and trashed=false", 
                        pageSize=PAGESIZE).execute()

        files = response['files']
        nextPageToken = response.get('nextPageToken')
        
        while nextPageToken:
            response = DRIVE.files().list(q=f"'{folder_id}' in parents and mimeType = '{DRIVE_FOLDER_TYPE}' and trashed=false", 
                            pageSize=PAGESIZE, pageToken=nextPageToken).execute()
            nextPageToken = response.get('nextPageToken')
            files.extend(response.get('files', []))
        
        all_folders = [current_folder]
        
        folders_in_folder = [DriveFile(file['id'], file['name']) for file in files]
        
        for folder_in_folder in folders_in_folder:
            nested_folders = get_drive_nested_folders(folder_in_folder.name)
            
            all_folders.extend(nested_folders)
        
        if has_duplicates(all_folders):
            raise Exception(f'Folder {folder_name} has duplicate folder names {get_duplicates(all_folders)}')
        
        return set(all_folders)

    except Exception as ex:
        global EXECUTION_RESULT
        EXECUTION_RESULT = False
        traceback.print_exc()
        

def download_file(file_id, name, local_path):
    print(f'\nDownloading file {name}...')
    
    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))    
    request = DRIVE.files().get_media(fileId=file_id)
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    with io.open(local_path, 'wb') as f:
        fh.seek(0)
        f.write(fh.read())
        
    if done:
        config.CURRENT_LOAD_NUMBER += 1
        loaded = config.CURRENT_LOAD_NUMBER
        total = config.TOTAL_LOAD_NUMBER
        print_success(f'Downloaded {name} [{loaded / float(total) * 100 : .2f}% ({loaded}/{total}) ]')
    else:
        print_fail(f'FAILED download {name}')
        global EXECUTION_RESULT
        EXECUTION_RESULT = False
        raise Exception(f'Download fail {name}')
        

def delete_file(drive_file: DriveFile):
    try:
        print(f'\nDeleting file {drive_file.name}...')
        
        DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
        DRIVE.files().delete(fileId=drive_file.id).execute()
        
        
        config.CURRENT_LOAD_NUMBER += 1
        loaded = config.CURRENT_LOAD_NUMBER
        total = config.TOTAL_LOAD_NUMBER
        print_success(f'Deleted {drive_file.name} [{loaded / float(total) * 100 : .2f}% ({loaded}/{total}) ]')
    except Exception as ex:
        print_fail(ex)
        print_fail(f'FAILED to delete file {drive_file.name}')
        global EXECUTION_RESULT
        EXECUTION_RESULT = False
        traceback.print_exc()


def _get_id_by_name(name, parent_id=None):
    fixed_quotes_name = name.replace("'", "\\'")
    
    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    if parent_id == None:
        response = DRIVE.files().list(q=f"name='{ fixed_quotes_name }' and trashed=false").execute()
    else:
        response = DRIVE.files().list(q=f"'{parent_id}' in parents and name='{ fixed_quotes_name }' and trashed=false").execute()
    
    if len(response['files']) == 0:
        raise Exception(f'Name was not found "{name}"')
    
    if len(response['files']) > 1:
        raise Exception(f'Duplicate names "{name}"')
    return response['files'][0]['id']


def _get_folder_id_by_name(name, parent_id=None):
    fixed_quotes_name = name.replace("'", "\\'")
    
    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    if parent_id == None:
        response = DRIVE.files().list(q=f"name='{ fixed_quotes_name }' and trashed=false and mimeType = '{DRIVE_FOLDER_TYPE}'").execute()
    else:
        response = DRIVE.files().list(q=f"'{parent_id}' in parents and name='{ fixed_quotes_name }' and trashed=false and mimeType = '{DRIVE_FOLDER_TYPE}'").execute()
    
    if len(response['files']) == 0:
        raise Exception(f'Name was not found "{name}"')
    
    if len(response['files']) > 1:
        raise Exception(f'Duplicate names "{name}"')
    return response['files'][0]['id']


def get_item_by_name(files, name):
    files = list(filter(lambda x: x['name'] == name, files))
    if len(files) == 0:
        raise Exception(f'Item {name} was not found')
    if len(files) > 1:
        print(files)
        raise Exception(f'Duplicate {name} items')
    
    return files[0]


def fetch_from_local_to_drive(drive_set, local_set):
    print('Fetching for push...\n')
    upload = local_set - drive_set
    delete = drive_set - local_set    
    return upload, delete


def fetch_from_drive_to_local(drive_set, local_set):
    print('Fetching for pull...\n')
    download = drive_set - local_set 
    delete = local_set - drive_set 
    return download, delete


def test_items(drive_directory, local_directory):
    print_warning('\nTESTING LOCAL AND DRIVE FOLDERS\n')
    
    drive_folders = get_drive_nested_folders(drive_directory)
            
    local_folders = local_helper.get_local_nested_folders(local_directory)
    
    if local_folders != drive_folders:
        raise Exception(f'Local and drive folders are not equal')
    
    push_dict = {}
    
    is_up_to_date = True
    
    for drive_folder in drive_folders:
        name = drive_folder.name
        local_folder = local_helper.get_item_by_name(local_folders, name)
        
        drive_file_set = get_folder_items(name)
        
        local_file_set = local_helper.get_local_directory_files(local_folder.path)
        
        upload, delete = fetch_from_local_to_drive(drive_set=drive_file_set,
                                            local_set=local_file_set)
        push_dict[drive_folder] = {}
        push_dict[drive_folder][UPLOAD_TO_DRIVE_KEY] = upload
        push_dict[drive_folder][DELETE_ON_DRIVE_KEY] = delete
        
        if is_up_to_date and (len(upload) != 0 or len(delete) != 0):
            is_up_to_date = False
            
    return is_up_to_date


def has_duplicates(input_list):
    return len(input_list) != len(set(input_list))


def get_duplicates(input_list):
    return str([item for item, count in collections.Counter(input_list).items() if count > 1])


def get_amount_of_files(folders):
    res = 0
    for folder in folders:
        if UPLOAD_TO_DRIVE_KEY in folders[folder]:
            res += len(folders[folder][UPLOAD_TO_DRIVE_KEY])
            
        if DELETE_ON_DRIVE_KEY in folders[folder]:
            res += len(folders[folder][DELETE_ON_DRIVE_KEY])
            
        if DOWNLOAD_FROM_DRIVE_KEY in folders[folder]:
            res += len(folders[folder][DOWNLOAD_FROM_DRIVE_KEY])
            
        if DELETE_IN_LOCAL_KEY in folders[folder]:
            res += len(folders[folder][DELETE_IN_LOCAL_KEY])
    
    return res
