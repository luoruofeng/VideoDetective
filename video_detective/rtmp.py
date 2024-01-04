import cv2
import threading
import util

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

# IOC拉流
class RTMPSrv:
    def __init__(self, rtmp_url,stop_event:threading.Event,id=1):
        self.rtmp_url = rtmp_url
        self.id = id
        self.stop_event = stop_event
        self.video_capture = None

    def stop(self):
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()

    def read(self, frame_callback=None)->list:
        try:
            self.capture = cv2.VideoCapture(self.rtmp_url)
            if not self.capture.isOpened():
                raise ValueError(f"拉流OpenVC-无法打开流 id:{id} url:{self.rtmp_url}")
            # 拉流
            print(f"拉流OpenVC-开始 id:{self.id}")
            while not self.stop_event.is_set():
                ret, frame = self.capture.read()
                if not ret:
                    break
                frame_callback(ret, frame)
                if frame_callback is not None:
                    # cv2.imshow('RTMP Stream', frame)
                    if cv2.waitKey(util.ConfigSingleton().yolo['refresh_time_ms']) & 0xFF == ord('q'):
                        break
                else:
                    raise ValueError(f"拉流OpenVC-没有设置回调函数 id:{self.id} rtmp_url:{self.rtmp_url}")   
        except Exception as e:
            print(f"拉流OpenVC-错误 id:{self.id} Exception occurred: {e}")
            return
        finally:
            print(f"拉流OpenVC-结束 id:{self.id}")


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
