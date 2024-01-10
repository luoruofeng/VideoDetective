from setuptools import setup, find_packages
import os

# 获取项目目录
project_dir = os.path.abspath('.')

with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setup(
    name='VideoDetective',
    version='0.0.1',
    author="luoruofeng",
    url="https://github.com/luoruofeng/VideoDetective",
    packages=find_packages(where=".",exclude=['video_detective.tests'],include = ("*",)),
    python_requires='>=3.10',
    install_requires=requirements,
    package_dir={'': project_dir},
    data_files=[("Lib/site-packages/video_detective/config", #打包后将配置文件复制到指定的路径。路径需要是打包后的Lib/site-packages/{name}为存放配置文件的父路径
                 [
                     "./config/init_video_detective_prompt_children.json",
                    "./config/init_video_detective_prompt_continue.json",
                    "./config/init_video_detective_prompt_detail.json",
                    "./config/init_video_detective_prompt_documentary_continue.json",
                    "./config/init_video_detective_prompt.json",
                    "./config/request.json"
                ]
                ),("Lib/site-packages/video_detective/source", 
                 [
                     "./source/lv.png",
                ]
                )],
    entry_points={
        'console_scripts': [
            'vd-web = video_detective.web:video_detective_launch',
        ],
    },
)
