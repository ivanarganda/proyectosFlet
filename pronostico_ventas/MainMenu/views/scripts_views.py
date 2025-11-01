import os

def init_metadata():
    return {
            "path": os.path.abspath(__file__),
            "folder": os.path.dirname(os.path.abspath(__file__)).split("\\")[-1],
            "file": os.path.basename(__file__)
        }
     