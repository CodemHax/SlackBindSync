import os


def get_root():
    current_file = os.path.abspath(__file__)
    api_dir = os.path.dirname(current_file)
    src_dir = os.path.dirname(api_dir)
    return os.path.dirname(src_dir)

