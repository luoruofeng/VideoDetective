import ffmpeg
import cv2
import threading
import util
from collections import deque
import queue
import os

# 为阻塞deque的get函数
class BlockingDeque:
    def __init__(self, maxlen):
        self.deque = deque(maxlen=maxlen)
        self.condition = threading.Condition()

    def put(self, item):
        with self.condition:
            self.deque.append(item)
            self.condition.notify()

    def get(self):
        with self.condition:
            while not self.deque:
                self.condition.wait()
            return self.deque.popleft()

# 常规拉流
class RTMPPuller:
    def __init__(self, rtmp_url,id,stop_event:threading.Event):
        self.rtmp_url = rtmp_url
        self.id = id
        self.capture = None
        self.stop_event = stop_event

    #打开RTMP流，并在一个新线程中开始读取帧。
    def start(self):
        self.capture = cv2.VideoCapture(self.rtmp_url)
        if not self.capture.isOpened():
            raise ValueError(f"拉流OpenVC-无法打开流 id:{self.id} url:{self.rtmp_url}")
        # 拉流
        try:
            print(f"拉流OpenVC-开始 id:{self.id}")
            while not self.stop_event.is_set():
                ret, frame = self.capture.read()
                if not ret:
                    break
                # Process the frame (e.g., display it or perform detection)
                # cv2.imshow('RTMP Stream', frame)
                if cv2.waitKey(util.ConfigSingleton().yolo['refresh_time_ms']) & 0xFF == ord('q'):
                    break
        except Exception as e:
            print(f"拉流OpenVC-错误 id:{self.id} Exception occurred: {e}")
            return
        finally:
            print(f"拉流OpenVC-结束 id:{self.id}")
            

    #停止读取流，并关闭与RTMP流的连接。
    def stop(self):
        if self.capture is not None:
            self.capture.release()
        # cv2.destroyAllWindows()
        print(f"拉流OpenVC-结束 id:{self.id}",)

# IOC拉流
class RTMPSrv:
    def __init__(self, rtmp_url,stop_event:threading.Event,id=1,cache_size=1024):
        self.rtmp_url = rtmp_url
        self.id = id
        self.stop_event = stop_event
        self.capture = None
        self.pull_cache_queue = BlockingDeque(maxlen=cache_size)
        self.exception_queue = queue.Queue()
        self.p_thread = None

    # 释放推流资源
    def stop_p_thread(self,process):
        if process is not None:
            process.stdin.close()
            process.wait()
    
    def processAndPush(self, frame_callback = None):
        try:
            stream_url = util.ConfigSingleton().detectives[util.ConfigSingleton().get_index_by_id(self.id)]["rtmp"]["push_stream"]
            # 获取视频源的属性
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            print(f"拉流OpenVC-处理推流线程-参数 id:{self.id} width:{width} height:{height} fps:{fps}")
            # 设置输出目的地为 /dev/null 或 NUL，取决于操作系统
            null_output = open(os.devnull, 'w')
            # 设置ffmpeg转码和推流的参数
            process = (
                ffmpeg
                .input('pipe:0', format='rawvideo', pix_fmt='bgr24', s='{}x{}'.format(width, height), r=fps)
                .output(stream_url, format='flv', vcodec='libx264', pix_fmt='yuv420p', preset='ultrafast')
                .overwrite_output()
                .run_async(pipe_stdin=True)
            )
            process.stdout = null_output
            process.stderr = null_output

            while not self.stop_event.is_set():
                ret, frame = self.pull_cache_queue.get()
                try:
                    frame = frame_callback(ret, frame)
                except Exception as e:
                    print("拉流OpenVC-处理推流线程-模型处理报错",e)
                if frame_callback is not None:
                    # cv2.imshow('RTMP Stream', frame)
                    # 将捕获的帧写入ffmpeg进程的标准输入
                    if process.poll() is None:
                        process.stdin.write(frame.tobytes())
                    if cv2.waitKey(util.ConfigSingleton().yolo['refresh_time_ms']) & 0xFF == ord('q'):
                        break
                else:
                    raise ValueError(f"拉流OpenVC-处理推流线程-没有设置回调函数 id:{self.id} rtmp_url:{self.rtmp_url}")    
        finally:
            if process is not None:
                self.stop_p_thread(process)
            print(f"拉流OpenVC-处理推流线程-结束 id:{self.id}")
        
    def read(self, frame_callback=None)->list:
        # 准备拉流
        self.capture = cv2.VideoCapture(self.rtmp_url)
        if not self.capture.isOpened():
            raise ValueError(f"拉流OpenVC-无法打开流 id:{self.id} url:{self.rtmp_url}")
        try:
            if not self.capture.isOpened():
                raise ValueError(f"拉流OpenVC-无法打开流 id:{self.id} url:{self.rtmp_url}")
            self.capture = cv2.VideoCapture(self.rtmp_url)

            # 准备处理并且推流
            if self.p_thread is None:
                p_thread = threading.Thread(target=self.processAndPush,args=(frame_callback,))
                p_thread.daemon = True
                p_thread.start()
            elif self.p_thread.is_alive() == False:
                raise ValueError(f"拉流OpenVC-处理推流线程退出 id:{self.id} url:{self.rtmp_url}")

            # 拉流
            print(f"拉流OpenVC-开始 id:{self.id}")
            while not self.stop_event.is_set():
                ret, frame = self.capture.read()
                self.pull_cache_queue.put((ret, frame))
                if not ret:
                    break                
        except Exception as e:
            print(f"拉流OpenVC-错误 id:{self.id} Exception occurred: {e}")
            return
        finally:
            print(f"拉流OpenVC-结束 id:{self.id}")
            if self.capture is not None:
                self.capture.release()


if __name__ == "__main__":
    # Usage example
    rtmp_url = 'rtmp://example.com/live/stream1'
    rtmp_puller = RTMPPuller(rtmp_url)

    # Start pulling the RTMP stream
    rtmp_puller.start()

    # Do something else while the stream is being pulled...
    # ...

    # Stop pulling the stream when done
    rtmp_puller.stop()
