from flask import Flask, render_template
import threading
import util
from rtmp import RTMPPuller
from argparse import ArgumentParser
import signal
import sys

DEFAULT_CONFIG_PATH = '../config/config.yaml'

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

app = Flask(__name__)

ALL_CHILDREN_THREAD = []
SHUT_DOWN_EVENT = threading.Event()

def rtmp_worker(id, stream_url):
    number_of_retry_short2long = util.ConfigSingleton().pull_rtmp['number_of_retry_short2long']
    short_wait_retry_seconds = util.ConfigSingleton().pull_rtmp['short_wait_retry_seconds']
    long_wait_retry_seconds = util.ConfigSingleton().pull_rtmp['long_wait_retry_seconds']
    retries = 0
    try:
        puller = RTMPPuller(stream_url, id, SHUT_DOWN_EVENT)
        while not SHUT_DOWN_EVENT.is_set():
            try:
                puller.start()
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
        util.ConfigSingleton().reload()
        print(f'拉流worker被移除 stream_url:{stream_url}, id:{id} ')
        print(f'拉流workers: {util.ConfigSingleton().detectives}')

def start_rtmp_workers():
    #启动 rtmp 拉流线程
    for i in range(len(util.ConfigSingleton().detectives)):
        det = util.ConfigSingleton().detectives[i]
        t = threading.Thread(target=rtmp_worker, args=(det['id'], det['rtmp']['pull_stream'],))
        t.setDaemon(util.ConfigSingleton().pull_rtmp['daemon'])
        ALL_CHILDREN_THREAD.append(t)
        t.start()

@app.route('/')
def index():
    # 这里的index.html应该包含播放RTMP流的逻辑
    return render_template('index.html')

@app.route('/stream/<int:stream_id>')
def stream(stream_id):
    # 根据stream_id获取对应的RTMP流地址
    stream_url = util.ConfigSingleton().detectives[stream_id]['rtmp']['push_stream']
    # 将stream_url传递给前端页面进行播放
    return render_template('stream.html', stream_url=stream_url)

def signal_handler(sig, frame):
    SHUT_DOWN_EVENT.set()
    print(f"用户结束程序 当前子线程:{ALL_CHILDREN_THREAD} 子线程数据:{len(ALL_CHILDREN_THREAD)}")
    # 停止RTMP工作线程
    if not util.ConfigSingleton().pull_rtmp['daemon']:
        for thread in ALL_CHILDREN_THREAD:
            print(f"子线程-等待结束 thread:{thread}")
            thread.join()  # 等待线程结束
            print(f"子线程-结束 thread:{thread}")
    print("good bye!")
    sys.exit(0)

#TODO 添加对config的监控 修改后可以修改拉流文件

def video_detective_launch():
    args = _get_args()
    print(f'拉流workers: {util.ConfigSingleton().detectives}')
    start_rtmp_workers()

    signal.signal(signal.SIGINT, signal_handler)  # 注册Ctrl+C信号处理程序

    app.run(debug=args.debug, host=args.server_name, port=args.server_port) 


if __name__ == '__main__':
    video_detective_launch()