from datetime import datetime
import os
import yaml
from threading import Lock
import cv2
import threading

# Usage
# ConfigSingleton().detectives
# ConfigSingleton().yolo
# ConfigSingleton().pull_rtmp
# ConfigSingleton().server
class ConfigSingleton:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigSingleton, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path=None):
        if config_path == None:
            dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(dir,'config/config.yaml') 

        if self._initialized:
            return
        self._initialized = True
        self.config_path = config_path
        with open(config_path, 'r', encoding="utf8") as file:
            self.config = yaml.safe_load(file)
        
    def get_detectives_changed(self, other):
        changed = []
        ods  = other["detectives"]
        #新增和修改的detectives
        for d in self.detectives:
            if d["id"] not in [item["id"] for item in ods]:
                changed.append(d)
                continue
            else:
                od = list(filter(lambda obj : obj["id"] == d["id"], ods))[0]
                if (od["rtmp"]["pull_stream"],od["rtmp"]["push_stream"],od["rtmp"]["play_url"],od["monitoring_topics"],od["polygon_coordinates"]) == (d["rtmp"]["pull_stream"],d["rtmp"]["push_stream"],d["rtmp"]["play_url"],d["monitoring_topics"],d["polygon_coordinates"]):
                    continue
                else:
                    changed.append(d)
        #删除的detectives
        for o in ods:
            if o["id"] not in [item["id"] for item in self.detectives]:
                o['rtmp']["push_stream"],o['rtmp']["pull_stream"],o['rtmp']["play_url"],o["monitoring_topics"],o["polygon_coordinates"] = None,None,None,None,None
                changed.append(o)
                continue
        return changed
        
    def contain_pull_rtmp(self, val: str):
        self.reload()
        for o in self.detectives:
            if o["rtmp"]["pull_stream"] == val:
                return True
        return False
        

    def get_index_by_id(self,id:str)->int:
        index = 0
        for det in self.detectives:
            print(det)
            if det["id"] == id:
                return index
            index += 1
        return None

    
    def reload(self, config_path=None):
        if config_path == None:
            dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(dir,'config/config.yaml') 
        with self._lock:
            # 清除当前配置
            self.config = None
            self._initialized = False
            
            # 重新读取配置文件
            with open(config_path, 'r', encoding="utf8") as file:
                self.config = yaml.safe_load(file)
            
            # 设置重新初始化标志
            self._initialized = True
        
    @property
    def detectives(self):
        return self.config['detectives']

    @property
    def yolo(self):
        return self.config['yolo']
    
    @property
    def pull_rtmp(self):
        return self.config['pull_rtmp']
    
    @property
    def server(self):
        return self.config['server']

def calculate_center(xmin, ymin, xmax, ymax):
    # 计算中心点坐标
    center_x = (xmin + xmax) // 2
    center_y = (ymin + ymax) // 2
    return center_x, center_y

@staticmethod
def format_time(time, format_str:str="%Y-%m-%d %H:%M:%S"):
    """
    Formats a datetime object into a string based on the provided format string.

    :param time: datetime object to format.
    :param format_str: String defining the desired format.
    :return: Formatted time string.
    """
    time_obj = datetime.fromtimestamp(time)
    return time_obj.strftime(format_str)



def print_all_threads():
    # 获取当前活动的线程列表
    current_threads = threading.enumerate()
    
    # 打印每个线程的信息
    for thread in current_threads:
        print(f"Thread ID: {thread.ident}, Name: {thread.name}, Alive: {thread.is_alive()}")

# 示例使用
if __name__ == "__main__":
    xmin, ymin, xmax, ymax = 100, 150, 200, 250  # 举例目标框的坐标
    center_x, center_y = calculate_center(xmin, ymin, xmax, ymax)
    print(f"目标框的中心点坐标为 ({center_x}, {center_y})")

def get_fps(video_path):
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    # 获取帧率
    fps = cap.get(cv2.CAP_PROP_FPS)
    # 释放视频对象
    cap.release()
    return fps



# 使用例子
# safe_dict = SafeDict({'a': 1, 'b': 2})
# print(safe_dict['a'])  # 输出: 1
# print(safe_dict['c'])  # 输出: None
class SafeDict(dict):
    def __getitem__(self, key):
        return self.get(key, None)
