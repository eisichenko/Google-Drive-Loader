import io
from os.path import join

from googleapiclient import discovery
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools

from config import *
from helpers import local_helper, message_helper, set_helper
from helpers.message_helper import print_warning
from helpers.models import *
from helpers.validation_helper import is_valid_name, INVALID_CHARACTERS

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


def get_account_info() -> UserAccount:
    about = DRIVE.about().get(fields='user').execute()
    return UserAccount(email=about['user']['emailAddress'],
                       display_name=about['user']['displayName'])


def create_folder(root_folder: DriveFile, name: str) -> DriveFile:
    if not is_valid_name(name):
        raise Exception(f'Invalid drive folder name {name}. Invalid characters {INVALID_CHARACTERS}')

    file_metadata = {
        'name': name,
        'parents': [root_folder.id],
        'mimeType': 'application/vnd.google-apps.folder'
    }

    folder_response = DRIVE.files().create(body=file_metadata, fields='id, name').execute()
    new_folder = DriveFile(folder_response['id'], folder_response['name'], root_folder)
    root_folder.child_folders.add(new_folder)
    return new_folder


def upload_file(local_file: LocalFile, drive_folder: DriveFile) -> DriveFile:
    if not is_valid_name(local_file.name):
        raise Exception(f'Invalid local file name {local_file.absolute_local_path}. Invalid characters {INVALID_CHARACTERS}')

    file_metadata = {
        'name': local_file.name,
        'parents': [drive_folder.id]
    }

    media = MediaFileUpload(
        local_file.absolute_local_path,
        resumable=True
    )

    drive_file_response = DRIVE.files().create(body=file_metadata, media_body=media, fields='id, name').execute()

    if drive_file_response is None:
        raise Exception(f"Couldn't upload file {local_file}")

    return DriveFile(drive_file_response['id'], drive_file_response['name'], drive_folder)


def get_drive_folders_and_files(root_folder: DriveFile, parent: DriveFile = None) -> set[DriveFile]:
    print(f'\nGetting nested folders and files from drive folder {root_folder}...')

    query = f"'{root_folder.id}' in parents and trashed=false"
    fields = 'nextPageToken, files(id, name, size, mimeType)'

    folders_and_files_response = DRIVE.files().list(
        q=query,
        fields=fields,
        pageSize=PAGESIZE).execute()

    all_folders_and_files_response = folders_and_files_response['files']
    next_page_token = folders_and_files_response.get('nextPageToken')

    while next_page_token:
        folders_and_files_response = DRIVE.files().list(
            q=query,
            fields=fields,
            pageSize=PAGESIZE, pageToken=next_page_token).execute()
        next_page_token = folders_and_files_response.get('nextPageToken')
        all_folders_and_files_response.extend(folders_and_files_response.get('files', []))

    nested_folders = set()

    for response in all_folders_and_files_response:
        if response['mimeType'] == DRIVE_FOLDER_TYPE:
            new_file: DriveFile = DriveFile(response['id'], response['name'], parent=root_folder)
            if new_file in nested_folders:
                raise Exception(f'Duplicate drive folders {new_file}')
            nested_folders.add(new_file)
            root_folder.child_folders.add(new_file)
            nested_folders.update(get_drive_folders_and_files(new_file, root_folder))
        else:
            new_file: DriveFile = DriveFile(response['id'],
                                            response['name'],
                                            parent=root_folder,
                                            size=response['size'])
            if new_file in root_folder.child_files:
                raise Exception(f'Duplicate drive files {new_file}')
            root_folder.child_files.add(new_file)

    if parent is None:
        if root_folder in nested_folders:
            raise Exception(f'Duplicate drive folders {root_folder}')
        nested_folders.add(root_folder)

    return nested_folders


def download_file(drive_file: DriveFile, local_folder: LocalFile) -> None:
    if not is_valid_name(drive_file.name):
        raise Exception(f'Invalid drive file name {drive_file.absolute_drive_path}. Invalid characters {INVALID_CHARACTERS}')

    local_absolute_path = join(local_folder.absolute_local_path, drive_file.name)

    request = DRIVE.files().get_media(fileId=drive_file.id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    with io.open(local_absolute_path, 'wb') as f:
        fh.seek(0)
        f.write(fh.read())

    if not done:
        raise Exception(f'FAILED downloading drive file {drive_file.name}')


def delete_file(drive_file: DriveFile) -> None:
    try:
        DRIVE.files().delete(fileId=drive_file.id).execute()
        if drive_file in drive_file.parent.child_folders:
            drive_file.parent.child_folders.remove(drive_file)
        if drive_file in drive_file.parent.child_files:
            drive_file.parent.child_files.remove(drive_file)
    except HttpError:
        pass


def create_drive_folders_from_local(drive_root: DriveFile, folders_to_create: set[LocalFile]) -> None:
    for local_folder in folders_to_create:
        local_folder: LocalFile
        if local_folder.parent.absolute_drive_path == drive_root.absolute_drive_path:
            print(f'\nCreating drive folder {local_folder.absolute_drive_path}...')
            new_folder: DriveFile = create_folder(drive_root, local_folder.name)
            message_helper.print_success(f'CREATED drive folder {new_folder}')

    for drive_folder in drive_root.child_folders:
        drive_folder: DriveFile
        create_drive_folders_from_local(drive_folder, folders_to_create)


def get_file_by_name(name: str, is_folder: bool) -> DriveFile:
    name = fix_quotes(name)

    if is_folder:
        files = DRIVE.files().list(q=f"name = '{name}' and trashed = false and mimeType = '{DRIVE_FOLDER_TYPE}'",
                                   fields='files(id, name)').execute()
    else:
        files = DRIVE.files().list(q=f"name = '{name}' and trashed = false and mimeType != '{DRIVE_FOLDER_TYPE}'",
                                   fields='files(id, name, size)').execute()

    if len(files['files']) == 0:
        raise Exception(f'Drive file name "{name}" was not found')

    if len(files['files']) > 1:
        raise Exception(f'Multiple drive files with name "{name}"')

    file_id = files['files'][0]['id']
    file_name = files['files'][0]['name']

    res = DriveFile(file_id=file_id, name=file_name, parent=None)

    return res


def fetch_from_local_to_drive(drive_set: set[DriveFile], local_set: set[LocalFile]):
    upload: set[LocalFile] = local_set - drive_set
    delete: set[DriveFile] = drive_set - local_set
    return upload, delete


def fetch_from_drive_to_local(drive_set: set[DriveFile], local_set: set[LocalFile]):
    download: set[DriveFile] = drive_set - local_set
    delete: set[LocalFile] = local_set - drive_set
    return download, delete


def test_items(drive_root_name: str, local_root_path: str) -> bool:
    print_warning('\nCOMPARING LOCAL AND DRIVE FOLDERS...\n')

    drive_root: DriveFile = get_file_by_name(drive_root_name, is_folder=True)
    local_root: LocalFile = LocalFile(local_root_path, parent=None)

    drive_folders = get_drive_folders_and_files(drive_root)
    local_folders = local_helper.get_local_folders(local_root)

    if local_folders != drive_folders:
        print(f'\nLocal and drive folders are not equal')
        return False

    comparing_dict = {}

    for drive_folder in drive_folders:
        absolute_drive_path = drive_folder.absolute_drive_path
        local_folder = set_helper.get_from_set_by_string(local_folders, absolute_drive_path)

        drive_file_set = drive_folder.child_files
        local_file_set = local_helper.get_folder_files(local_folder)

        upload, delete = fetch_from_local_to_drive(
            drive_set=drive_file_set,
            local_set=local_file_set
        )

        if len(upload) > 0 or len(delete) > 0:
            comparing_dict[drive_folder] = {}
            comparing_dict[drive_folder][UPLOAD_TO_DRIVE_KEY] = upload
            comparing_dict[drive_folder][DELETE_ON_DRIVE_KEY] = delete

    if len(comparing_dict) > 0:
        print(f'Not equal folders: {comparing_dict}')

    return len(comparing_dict) == 0


def fix_quotes(s: str) -> str:
    if "\\'" not in s and "'" in s:
        return s.replace("'", "\\'")
    return s
