import urllib.request
import tempfile
import tarfile
import os

def download_file(url, destination):
    """Скачивает файл по URL"""
    urllib.request.urlretrieve(url, destination)

def extract_tar_gz(archive_path, extract_dir):
    """Распаковывает tar.gz архив"""
    os.makedirs(extract_dir, exist_ok=True)
    with tarfile.open(archive_path, 'r:gz') as tar:
        tar.extractall(extract_dir)