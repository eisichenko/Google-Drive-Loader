from pathlib import Path


class AbstractFile:
    def __init__(self, absolute_path: str):
        self.absolute_path = absolute_path
        self.name = Path(absolute_path).name

    def __eq__(self, other):
        if not isinstance(other, AbstractFile):
            return False

        if other is None:
            return self.absolute_path is None

        other: AbstractFile

        return self.absolute_path == other.absolute_path

    def __hash__(self):
        return self.absolute_path.__hash__()

    def __str__(self):
        return self.absolute_path

    def __repr__(self):
        return self.absolute_path


class DriveFile(AbstractFile):
    def __init__(self, file_id: str, absolute_path: str):
        super().__init__(absolute_path)
        self.id = file_id


class LocalFile(AbstractFile):
    def __init__(self, absolute_path: str):
        super().__init__(absolute_path)
