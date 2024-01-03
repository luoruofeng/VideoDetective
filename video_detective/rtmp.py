import cv2
import threading
import util

class RTMPPuller:
    def __init__(self, rtmp_url,id,stop_event:threading.Event):
        self.rtmp_url = rtmp_url
        self.id = id
        self.capture = None
        self.thread = None
        self.stop_event = stop_event

    #打开RTMP流，并在一个新线程中开始读取帧。
    def start(self):
        self.capture = cv2.VideoCapture(self.rtmp_url)
        if not self.capture.isOpened():
            raise ValueError(f"拉流OpenVC-无法打开流 id:{id} url:{self.rtmp_url}")
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


class RTMPSrv:
    def __init__(self, file_path:str,callback_interval =1000):
        self.file_path = file_path
        self.video_capture = cv2.VideoCapture(self.file_path)
        self.stop_flag = False
        self.callback_interval =callback_interval 
        self.last_callback_time = time.time()  # 记录上一次调用回调函数的时间

    def stop(self):
        self.stop_flag = True

        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()

    def read(self, frame_callback=None)->list:
        try:
            self.video_capture = cv2.VideoCapture(self.file_path)
            if not self.video_capture.isOpened():
                raise FileNotFoundError(f"Error: Unable to open video file at {self.file_path}")

            while not self.stop_flag:
                ret, frame = self.video_capture.read()
                if not ret:
                    break

                # 处理视频帧的回调函数
                if frame_callback is not None:
                    current_time = time.time()
                    if current_time - self.last_callback_time >= self.callback_interval / 1000:
                        print(util.format_time(current_time))
                        frame_callback(ret, frame)
                        self.last_callback_time = current_time
                if cv2.waitKey(util.ConfigSingleton().yolo['refresh_time_ms']) & 0xFF == ord('q'):
                    self.stop()  # 调用 stop 方法停止播放
                    break

            self.stop_flag = False  # 重置标志位

        except Exception as e:
            print(f"An error occurred: {e}")


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
