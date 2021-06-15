from push import creds, EXECUTION_RESULT
from googleapiclient import discovery
from httplib2 import Http
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from config import *
import io
from threading import Lock
import local_helper

print_lock = Lock()


class bcolors:
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def lock_print(*a, **b):
    """Thread safe print function"""
    with print_lock:
        print(*a, **b)


def print_success(string):
    lock_print(bcolors.GREEN + bcolors.BOLD + str(string) + bcolors.ENDC)


def print_fail(string):
    lock_print(bcolors.FAIL + bcolors.BOLD + str(string) + bcolors.ENDC)


def print_cyan(string):
    lock_print(bcolors.CYAN + bcolors.BOLD + str(string) + bcolors.ENDC)


def print_warning(string):
    lock_print(bcolors.WARNING + bcolors.BOLD + str(string) + bcolors.ENDC)


def get_all_files():
    
    lock_print('\nGetting all files...\n')

    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    response = DRIVE.files().list(q='trashed=false', pageSize=PAGESIZE).execute()
    
    files = response.get('files', [])
    nextPageToken = response.get('nextPageToken')

    while nextPageToken:
        response = DRIVE.files().list(q='trashed=false', pageSize=PAGESIZE, pageToken=nextPageToken).execute()
        nextPageToken = response.get('nextPageToken')
        files.extend(response.get('files', []))
    
    return files


def upload_file(target_name, source_name, folder_name=None):
    try:
        if folder_name != None:
            folder_id = _get_id_by_name(folder_name)
            file_metadata = { 'name': target_name,
                              'parents': [folder_id]
                            }
        else:
            file_metadata = { 'name': target_name }
        
        lock_print(f'\nUploading file {source_name} --> {target_name}...\n')
        
        media = MediaFileUpload(source_name,
                                resumable=True)
        
        DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
        file = DRIVE.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        
        if file:
            print_success(f'File {file["name"]} UPLOADED (id {file["id"]})')
        else:
            raise Exception('Could not upload file')
    except Exception as ex:
        print_fail(f'File {source_name} FAIL UPLOAD')
        print_fail(ex)
        global EXECUTION_RESULT
        EXECUTION_RESULT = False
        

def get_folder_items(name):
    try:
        lock_print(f'\nGetting files from folder {name}...\n')
        
        folder_id = _get_id_by_name(name)
        
        DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
        response = DRIVE.files().list(q=f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed=false", 
                        pageSize=PAGESIZE).execute()

        files = response['files']
        nextPageToken = response.get('nextPageToken')
        
        while nextPageToken:
            response = DRIVE.files().list(q=f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed=false", 
                            pageSize=PAGESIZE, pageToken=nextPageToken).execute()
            nextPageToken = response.get('nextPageToken')
            files.extend(response.get('files', []))
        
        return files

    except Exception as ex:
        print_fail(ex)
        global EXECUTION_RESULT
        EXECUTION_RESULT = False
        

def download_file(file_id, filename, name):
    lock_print(f'\nDownloading file {name}...', end=' ')
    
    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))    
    request = DRIVE.files().get_media(fileId=file_id)
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    with io.open(filename, 'wb') as f:
        fh.seek(0)
        f.write(fh.read())

    lock_print()
        
    if done:
        print_success(f'Downloaded {name}')
    else:
        print_fail(f'FAILED download {name}')
        global EXECUTION_RESULT
        EXECUTION_RESULT = False
        

def delete_file(file_id, filename):
    try:
        lock_print(f'\nDeleting file {filename}...')
        
        DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
        DRIVE.files().delete(fileId=file_id).execute()
        
        print_success(f'File {filename} was successfully deleted!')
    except Exception as ex:
        print_fail(ex)
        print_fail(f'FAILED to delete file {filename}')
        global EXECUTION_RESULT
        EXECUTION_RESULT = False


def _get_id_by_name(name):
    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
    response = DRIVE.files().list(q=f"name='{name}' and trashed=false").execute()
    
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


def fetch_from_local_to_drive(drive_names_set, local_names_set):
    lock_print('Fetching for push...\n')
    upload = local_names_set - drive_names_set
    delete = drive_names_set - local_names_set    
    return upload, delete


def fetch_from_drive_to_local(drive_names_set, local_names_set):
    lock_print('Fetching for pull...\n')
    download = drive_names_set - local_names_set 
    delete = local_names_set - drive_names_set 
    return download, delete


def test_number_of_items(drive_directory, local_directory):
    drive_items = get_folder_items(drive_directory)
    local_items_names = local_helper.get_local_directory_files(local_directory)
    res = len(drive_items) == len(local_items_names)
    
    if res:
        print_success(f'{len(drive_items)} (drive) == {len(local_items_names)} (local)')
    else:
        print_fail(f'{len(drive_items)} != {len(local_items_names)}')
        global EXECUTION_RESULT
        EXECUTION_RESULT = False

    return res