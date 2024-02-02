# VideoDetective
监控流媒体物体：人 火 烟。
   
依赖：
1. ffmpeg
2. CUDA

## 运行
```
sudo apt-get install ffmpeg

pip install -r requirements.txt
python .\video_detective\web.py
```
指定config文件路径和端口
```shell
python .\video_detective\web.py -c .\c.yaml -p 8333
```

## 安装vd-web
根据CUDA版本安装Torch依赖,参考[Pytorch安装](https://pytorch.org/get-started/locally/)
```shell
pip install torch -f https://download.pytorch.org/whl/cu121/torch-1.12.0%2Bcu121-cp38-cp38-linux_x86_64.whl
pip install torchvision -f https://download.pytorch.org/whl/cu121/torchvision-0.13.0%2Bcu121-cp38-cp38-linux_x86_64.whl
pip install torchaudio -f https://download.pytorch.org/whl/cu121/torchaudio-0.12.0%2Bcu121-cp38-cp38-linux_x86_64.whl
```

python安装vc命令
```
pip install .
```

## 编译wheel
编译前：根据运行的操作系统来注释setup.py中的INSTALL_PATH属性。
```
pip install setuptools wheel

python setup.py bdist_wheel
```


