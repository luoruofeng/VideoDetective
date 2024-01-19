import glob
from setuptools import setup, find_packages
import os

# 获取项目目录
project_dir = os.path.abspath('.')

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


INSTALL_PATH = "Lib/site-packages/video_detective/"
def get_install_path(r_path):
    return os.path.join(INSTALL_PATH, r_path)

# 需要递归所有文件夹下的文件路径
def recursive_list_files_folders(base_path):
    result = []
    for root, dirs, files in os.walk(base_path):
        folder_path = os.path.relpath(root, base_path)  # 获取相对于基本路径的文件夹路径
        file_paths = [os.path.join(base_path, folder_path, file) for file in files]  # 获取文件的相对路径
        result.append((get_install_path(os.path.join(base_path.split("/")[-1], folder_path)), file_paths))
    return result


setup(
    name='VideoDetective',
    version='0.0.1',
    author="luoruofeng",
    url="https://github.com/luoruofeng/VideoDetective",
    packages=find_packages(where=".",exclude=['video_detective.tests'],include = ("*",)),
    python_requires='>=3.10',
    install_requires=requirements,
    package_dir={'': project_dir},
    data_files=[(get_install_path("config"), #打包后将配置文件复制到指定的路径。路径需要是打包后的Lib/site-packages/{name}为存放配置文件的父路径
                 [
                     "./video_detective/config/config.yaml",
                ]
                ),(get_install_path("templates"), 
                 glob.glob("./video_detective/templates/**/*", recursive=True)
                ),(get_install_path("source"), 
                 glob.glob("./video_detective/source/**/*", recursive=True)
                )] + recursive_list_files_folders("video_detective/static") + recursive_list_files_folders("video_detective/pt"),
    entry_points={
        'console_scripts': [
            'vd-web = video_detective.web:video_detective_launch',
        ],
    },
)
