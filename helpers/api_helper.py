from helpers.message_helper import print_success, print_warning
from oauth2client import file, client, tools
from helpers.models import *
from googleapiclient import discovery
from httplib2 import Http
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from config import *
import config
import io
from helpers import local_helper
import collections

DRIVE_FOLDER_TYPE = 'application/vnd.google-apps.folder'

UPLOAD_TO_DRIVE_KEY = 'upload_to_drive'
DELETE_ON_DRIVE_KEY = 'delete_on_drive'
DOWNLOAD_FROM_DRIVE_KEY = 'download_from_drive'
DELETE_IN_LOCAL_KEY = 'delete_in_local'

SCOPES = 'https://www.googleapis.com/auth/drive'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_id.json', SCOPES)
    creds = tools.run_flow(flow, store)

DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))


def print_account_info() -> None:
    about = DRIVE.about().get(fields='user').execute()

    print_warning(f'\nCurrent account: {about["user"]["emailAddress"]}')
    print_warning(f'Account name: {about["user"]["displayName"]}')


def upload_file(target_name, source_name, folder: DriveFile):
    if folder is not None:
        file_metadata = {
            'name': target_name,
            'parents': [folder.id]
        }
    else:
        file_metadata = {'name': target_name}

    print(f'\nUploading file {source_name} --> {target_name}...\n')

    media = MediaFileUpload(
        source_name,
        resumable=True
    )

    drive_file = DRIVE.files().create(body=file_metadata, media_body=media, fields='id, name').execute()

    if drive_file is not None:
        config.CURRENT_LOAD_NUMBER += 1
        loaded = config.CURRENT_LOAD_NUMBER
        total = config.TOTAL_LOAD_NUMBER
        print_success(
            f'File {drive_file["name"]} UPLOADED (id {drive_file["id"]}) [{loaded / float(total) * 100 : .2f}% ({loaded}/{total}) ]')
    else:
        raise Exception(f"Couldn't upload file {source_name}")


def get_folder_items(folder_name) -> set:
    print(f'\nGetting files from folder {folder_name}...\n')

    folder_id = _get_id_by_name(folder_name)

    response = DRIVE.files().list(
        q=f"'{folder_id}' in parents and mimeType != '{DRIVE_FOLDER_TYPE}' and trashed=false",
        pageSize=PAGESIZE).execute()

    files = response['files']
    next_page_token = response.get('nextPageToken')

    while next_page_token:
        response = DRIVE.files().list(
            q=f"'{folder_id}' in parents and mimeType != '{DRIVE_FOLDER_TYPE}' and trashed=false",
            pageSize=PAGESIZE, pageToken=next_page_token).execute()
        next_page_token = response.get('nextPageToken')
        files.extend(response.get('files', []))

    drive_files = [DriveFile(drive_file['id'], drive_file['name']) for drive_file in files]

    if has_duplicates(drive_files):
        raise Exception(f'Duplicate files in drive folder {folder_name}')

    return set(drive_files)


def get_drive_nested_folders(folder_name) -> set:
    print(f'\nGetting nested folders from folder {folder_name}...\n')

    folder_id = _get_folder_id_by_name(folder_name)

    current_folder = DriveFile(folder_id, folder_name)

    response = DRIVE.files().list(
        q=f"'{folder_id}' in parents and mimeType = '{DRIVE_FOLDER_TYPE}' and trashed=false",
        pageSize=PAGESIZE).execute()

    files = response['files']
    next_page_token = response.get('nextPageToken')

    while next_page_token:
        response = DRIVE.files().list(
            q=f"'{folder_id}' in parents and mimeType = '{DRIVE_FOLDER_TYPE}' and trashed=false",
            pageSize=PAGESIZE, pageToken=next_page_token).execute()
        next_page_token = response.get('nextPageToken')
        files.extend(response.get('files', []))

    all_folders = [current_folder]

    folders_in_folder = [DriveFile(drive_file['id'], drive_file['name']) for drive_file in files]

    for folder_in_folder in folders_in_folder:
        nested_folders = get_drive_nested_folders(folder_in_folder.name)

        all_folders.extend(nested_folders)

    if has_duplicates(all_folders):
        raise Exception(f'Folder {folder_name} has duplicate folder names {get_duplicates(all_folders)}')

    return set(all_folders)


def download_file(file_id, name, local_path):
    print(f'\nDownloading file {name}...')

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
        raise Exception(f'FAILED download {name}')


def delete_file(drive_file: DriveFile):
    print(f'\nDeleting file {drive_file.name}...')

    DRIVE.files().delete(fileId=drive_file.id).execute()

    config.CURRENT_LOAD_NUMBER += 1
    loaded = config.CURRENT_LOAD_NUMBER
    total = config.TOTAL_LOAD_NUMBER
    print_success(f'Deleted {drive_file.name} [{loaded / float(total) * 100 : .2f}% ({loaded}/{total}) ]')

    raise Exception(f'FAILED to delete file {drive_file.name}')


def _get_id_by_name(name, parent_id=None):
    fixed_quotes_name = name.replace("'", "\\'")

    if parent_id is None:
        response = DRIVE.files().list(q=f"name='{fixed_quotes_name}' and trashed=false").execute()
    else:
        response = DRIVE.files().list(
            q=f"'{parent_id}' in parents and name='{fixed_quotes_name}' and trashed=false").execute()

    if len(response['files']) == 0:
        raise Exception(f'Name was not found "{name}"')

    if len(response['files']) > 1:
        raise Exception(f'Duplicate names "{name}"')
    return response['files'][0]['id']


def _get_folder_id_by_name(name, parent_id=None):
    fixed_quotes_name = name.replace("'", "\\'")

    if parent_id is None:
        response = DRIVE.files().list(
            q=f"name='{fixed_quotes_name}' and trashed=false and mimeType = '{DRIVE_FOLDER_TYPE}'").execute()
    else:
        response = DRIVE.files().list(
            q=f"'{parent_id}' in parents and name='{fixed_quotes_name}' and trashed=false and mimeType = '{DRIVE_FOLDER_TYPE}'").execute()

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
    upload = local_set - drive_set
    delete = drive_set - local_set
    return upload, delete


def fetch_from_drive_to_local(drive_set, local_set):
    download = drive_set - local_set
    delete = local_set - drive_set
    return download, delete


def test_items(drive_directory, local_directory):
    print_warning('\nCOMPARING LOCAL AND DRIVE FOLDERS\n')

    drive_folders = get_drive_nested_folders(drive_directory)

    local_folders = local_helper.get_local_nested_folders(local_directory)

    if local_folders != drive_folders:
        raise Exception(f'Local and drive folders are not equal')

    push_dict = {}

    is_up_to_date = True

    for drive_folder in drive_folders:
        name = drive_folder.absolute_path
        local_folder = local_helper.get_item_by_name(local_folders, name)

        drive_file_set = get_folder_items(name)

        local_file_set = local_helper.get_local_directory_files(local_folder.path)

        upload, delete = fetch_from_local_to_drive(
            drive_set=drive_file_set,
            local_set=local_file_set
        )

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
