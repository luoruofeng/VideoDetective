import sys
import os
# 获取当前脚本文件所在目录的路径
current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将当前脚本所在目录添加到sys.path中
sys.path.append(current_path)


from flask import Flask, render_template
import threading
from video_detective import util
from video_detective.rtmp import RTMPSrv
from argparse import ArgumentParser
import signal
import sys
from video_detective.detective import DetectiveSrv
from video_detective import detective
import torch

DEFAULT_CONFIG_PATH = '../config/config.yaml'
MODEL = None

def init_model():
    global MODEL  
    MODEL = torch.hub.load(util.ConfigSingleton().yolo['repo_or_dir'], util.ConfigSingleton().yolo['model'])  # or yolov5n - yolov5x6, custom
    print(f"初始化模型:{util.ConfigSingleton().yolo['repo_or_dir']}-{util.ConfigSingleton().yolo['model']}  类别列表:{MODEL.names}")
    
def _get_args():
    parser = ArgumentParser()
    parser.add_argument("-c", "--config-path", type=str, default=DEFAULT_CONFIG_PATH,
                        help="config yaml file path, default to %(default)r")
    parser.add_argument("--server-port", type=int, default=8000,
                        help="Demo server port.")
    parser.add_argument("--server-name", type=str, default="127.0.0.1",
                        help="Demo server name.")
    parser.add_argument("--debug", type=bool, default=False, help="server is debug model")

    # parser.add_argument("--cpu-only", action="store_true", help="Run demo with CPU only")
    # parser.add_argument("--share", action="store_true", default=False,
    #                     help="Create a publicly shareable link for the interface.")
    # parser.add_argument("--inbrowser", action="store_true", default=False,
    #                     help="Automatically launch the interface in a new tab on the default browser.")

    args = parser.parse_args()
    return args

app = Flask(__name__, static_folder='../static/', template_folder='../templates/')

ALL_CHILDREN_THREAD = []
SHUT_DOWN_EVENT = threading.Event()
SHUTDOWN_SIGNAL_RECEIVED = False # 设置一个标志，初始时为 False


class Worker():
    def __init__(self,id:int) -> None:
        self.id = id
        self.pull_stream = None
        self.push_stream = None
        self.play_url = None
        self.monitoring_topics = None
        self.polygon_coordinates = None
        self.play_srv = None
        self.ds:DetectiveSrv = None

    def set_props(self,pull_stream,push_stream,play_url,monitoring_topics,polygon_coordinates,):
        self.pull_stream = pull_stream
        self.push_stream = push_stream
        self.play_url = play_url
        self.monitoring_topics = monitoring_topics
        self.polygon_coordinates = polygon_coordinates
        self.play_srv = RTMPSrv(self.pull_stream ,stop_event=SHUT_DOWN_EVENT,id=self.id,cache_size=RTMP_CACHE_SIZE)
        self.ds = DetectiveSrv(play_srv=self.play_srv,id=id, model=MODEL, polygon=self.polygon_coordinates)

    def stop(self):
        self.play_srv.stop()


from typing import TypedDict


RTMP_WORKER_DICT:dict[str, Worker] = {} #k:id v:worker
RTMP_CACHE_SIZE = util.ConfigSingleton().pull_rtmp["cache_size"]

def init_workers():
    for i in range(len(util.ConfigSingleton().detectives)):
        det = util.ConfigSingleton().detectives[i]
        w = Worker(det['id'])
        w.set_props(det['rtmp']['pull_stream'], det['rtmp']['push_stream'], det['rtmp']['play_url'],det['monitoring_topics'],detective.get_polygon_coordinates(i))
        RTMP_WORKER_DICT[w.id]=w

number_of_retry_short2long = util.ConfigSingleton().pull_rtmp['number_of_retry_short2long']
short_wait_retry_seconds = util.ConfigSingleton().pull_rtmp['short_wait_retry_seconds']
long_wait_retry_seconds = util.ConfigSingleton().pull_rtmp['long_wait_retry_seconds']
def rtmp_worker(id, worker:Worker):
    retries = 0
    try:
        while not SHUT_DOWN_EVENT.is_set():
            try:
                worker.ds.start_detect()
            except Exception as e:
                util.ConfigSingleton().reload()
                retries += 1
                if retries < number_of_retry_short2long:
                    print(f"{short_wait_retry_seconds}秒后重试拉流 (Attempt {retries} of {number_of_retry_short2long})")
                    SHUT_DOWN_EVENT.wait(timeout=short_wait_retry_seconds)
                else:
                    print(f"{long_wait_retry_seconds}秒后重试拉流 (Attempt {retries} of {number_of_retry_short2long})")
                    SHUT_DOWN_EVENT.wait(timeout=long_wait_retry_seconds)
    finally:
        # util.ConfigSingleton().reload()
        # print(f'拉流workers: {util.ConfigSingleton().detectives}')
        print(f'拉流worker被移除 id:{id} stream_url:{worker.push_stream} ')


def start_rtmp_workers(workers:dict[str,Worker]):
    #启动 rtmp 拉流线程
    for id, worker in workers.items():
        worker.stop() #先停止原有worker的工作-停止原有线程
        if worker.pull_stream is not None:
            t = threading.Thread(target=rtmp_worker, args=(id, worker,))
            t.daemon = util.ConfigSingleton().pull_rtmp['daemon']
            ALL_CHILDREN_THREAD.append(t)
            t.start()

@app.route('/')
def index():
    # 这里的index.html应该包含播放RTMP流的逻辑
    return render_template('index.html')

@app.route('/stream/<int:stream_id>')
def stream(stream_id):
    index = util.ConfigSingleton().get_index_by_id(stream_id)
    # 根据stream_id获取对应的RTMP流地址
    stream_url = util.ConfigSingleton().detectives[index]['rtmp']['play_url']
    # 将stream_url传递给前端页面进行播放
    return render_template('stream.html', stream_url=stream_url)

CONFIG_SINGLETON =None
def init_check_config_thread():
    print("初始化检查配置文件线程")
    config_thread = threading.Thread(target=check_config_changes)
    config_thread.daemon = True
    config_thread.start()

# 定义一个函数来检查配置文件是否发生更改并更新全局变量
def check_config_changes():
    global CONFIG_SINGLETON
    if CONFIG_SINGLETON == None:
        CONFIG_SINGLETON = util.ConfigSingleton().config
    while not SHUT_DOWN_EVENT.is_set():
        util.ConfigSingleton().reload()
        new_config = util.ConfigSingleton().config
        changed = util.ConfigSingleton().get_detectives_changed(CONFIG_SINGLETON)
        changed_workers:dict[str,worker] = {}
        if len(changed) > 0:  # 检查新配置是否和之前的全局变量不同
            CONFIG_SINGLETON = new_config  # 更新全局变量
            for cd in changed:
                worker = RTMP_WORKER_DICT[cd["id"]]
                worker.set_props(cd["rtmp"]["pull_stream"],cd["rtmp"]["push_stream"],cd["rtmp"]["play_url"],cd["monitoring_topics"],cd["polygon_coordinates"])
                changed_workers[cd["id"]] = worker
            start_rtmp_workers(changed_workers)
            print(f"修改原有workers:{changed_workers}")
        SHUT_DOWN_EVENT.wait(util.ConfigSingleton().server["check_config_second"])


def signal_handler(sig, frame):
    global SHUTDOWN_SIGNAL_RECEIVED
    # 检查标志是否已经被设置
    if SHUTDOWN_SIGNAL_RECEIVED:
        # 如果已经接收到信号，直接返回
        return
    # 设置标志，表示信号已经接收
    SHUTDOWN_SIGNAL_RECEIVED = True
    print(f"用户结束程序-子线程数:{len(ALL_CHILDREN_THREAD)} 当前子线程:{ALL_CHILDREN_THREAD} ")
    global MODEL
    MODEL = None
    # util.print_all_threads()
    SHUT_DOWN_EVENT.set()
    # 停止RTMP工作线程
    if not util.ConfigSingleton().pull_rtmp['daemon']:
        for thread in ALL_CHILDREN_THREAD:
            print(f"子线程-等待结束 thread:{thread} {thread.is_alive()}")
            thread.join()  # 等待线程结束
            print(f"子线程-结束 thread:{thread}")
    print("good bye!")
    sys.exit(0)

#TODO 添加对config的监控 修改后可以修改拉流文件

def video_detective_launch():
    args = _get_args() #获取启动参数
    init_model() #初始化模块
    init_workers() #初始化rtmp workers
    print(f'拉流workers: {util.ConfigSingleton().detectives}')
    start_rtmp_workers(RTMP_WORKER_DICT)#开始rtmp拉流
    signal.signal(signal.SIGINT, signal_handler)  # 注册Ctrl+C信号处理程序
    init_check_config_thread()#初始化配置文件修改检查
    app.run(debug=args.debug, host=args.server_name, port=args.server_port)#web启动 


if __name__ == '__main__':
    video_detective_launch()