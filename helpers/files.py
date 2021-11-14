from pathlib import Path


class File:
    def __eq__(self, other):
        if other == None:
            return self.name == None
        return self.name == other.name
    
    def __hash__(self):
        return self.name.__hash__()
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name


class DriveFile(File):
    def __init__(self, id, name):
        self.id = id
        self.name = name

        
class LocalFile(File):
    def __init__(self, path):
        self.path = path
        self.name = Path(path).name
