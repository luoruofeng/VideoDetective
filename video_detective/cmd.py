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
# 设置一个标志，初始时为 False
shutdown_signal_received = False

def rtmp_worker(id, stream_url):
    number_of_retry_short2long = util.ConfigSingleton().pull_rtmp['number_of_retry_short2long']
    short_wait_retry_seconds = util.ConfigSingleton().pull_rtmp['short_wait_retry_seconds']
    long_wait_retry_seconds = util.ConfigSingleton().pull_rtmp['long_wait_retry_seconds']
    retries = 0
    try:
        # 常规拉流
        # puller = RTMPPuller(stream_url, id, SHUT_DOWN_EVENT)

        dindex = util.ConfigSingleton().get_index_by_id(id)
        polygon=detective.get_polygon_coordinates(dindex)
        play_srv = RTMPSrv(stream_url,stop_event=SHUT_DOWN_EVENT,id=id)
        ds = DetectiveSrv(play_srv=play_srv,id=id, model=MODEL, polygon=polygon)
        while not SHUT_DOWN_EVENT.is_set():
            try:
                # 常规拉流
                # puller.start()
                ds.detect_person()
            except Exception as e:
                print(f"拉流失败 id:{id} Exception occurred: {e}")
                if not util.ConfigSingleton().contain_pull_rtmp(stream_url):
                    print(f"config配置文件 detectives.rtmp.pull_stream不包含{stream_url}")
                    return
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
        print(f'拉流worker被移除 id:{id} stream_url:{stream_url} ')

def start_rtmp_workers():
    #启动 rtmp 拉流线程
    for i in range(len(util.ConfigSingleton().detectives)):
        det = util.ConfigSingleton().detectives[i]
        t = threading.Thread(target=rtmp_worker, args=(det['id'], det['rtmp']['pull_stream'],))
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

def signal_handler(sig, frame):
    global shutdown_signal_received
    # 检查标志是否已经被设置
    if shutdown_signal_received:
        # 如果已经接收到信号，直接返回
        return
    # 设置标志，表示信号已经接收
    shutdown_signal_received = True
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
    args = _get_args()
    init_model()
    print(f'拉流workers: {util.ConfigSingleton().detectives}')
    start_rtmp_workers()

    signal.signal(signal.SIGINT, signal_handler)  # 注册Ctrl+C信号处理程序

    app.run(debug=args.debug, host=args.server_name, port=args.server_port) 


if __name__ == '__main__':
    video_detective_launch()