from video_detective import util
import torch
import yolov5
import os

MODELS = []#已经加载了的所有YOLOv5模型

class Model():
    def __init__(self, model_name, repo_or_dir=None):
        if model_name is None:
            raise Exception("請在配置文件中配置正確的模型名稱和倉庫名或模型路徑")
        self.model_name = model_name
        self.repo_or_dir = repo_or_dir    

    
class ModelSrv():
    def __init__(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        pt_path = os.path.join(dir, 'pt')
        torch.hub.set_dir(pt_path)
        
        models = util.ConfigSingleton().yolo["models"]
        if models is None or len(models) < 1:
            raise Exception("請在配置文件中配置正確的模型名稱和倉庫名或模型路徑")
        for item in models:
            m = Model(model_name=item["name"], repo_or_dir=item["repo_or_dir"]) if "repo_or_dir" in item else Model(model_name=item["name"])
            m_loaded = None
            if m.repo_or_dir is None:
                m_loaded = torch.hub.load(os.path.dirname(yolov5.__file__), 'custom', os.path.join(pt_path, m.model_name), source='local')
                print(f"加載-本地 路径：{torch.hub.get_dir()} 模型:{m.model_name} 模型类别:{m_loaded.names}")
            else:
                m_loaded = torch.hub.load(m.repo_or_dir, m.model_name)
                print(f"加載-pytorch hub 路径：{torch.hub.get_dir()} 模型:{m.repo_or_dir} {m.model_name} 模型类别:{m_loaded.names}")
            MODELS.append(m_loaded)    