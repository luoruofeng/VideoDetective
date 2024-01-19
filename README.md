# VideoDetective
MP4和流的视频监控


## 运行
```
pip install -r requirements.txt
python .\video_detective\web.py
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



