import cv2
import time
import threading

class VideoSrv:
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
                        frame_callback(ret, frame)
                        self.last_callback_time = current_time

                if cv2.waitKey(1000) & 0xFF == ord('q'):
                    self.stop()  # 调用 stop 方法停止播放
                    break

            self.stop_flag = False  # 重置标志位

        except Exception as e:
            print(f"An error occurred: {e}")

    
    #获取视频的宽高
    def get_video_dimensions(self):
        try:
            self.video_capture = cv2.VideoCapture(self.file_path)
            if not self.video_capture.isOpened():
                raise FileNotFoundError(f"Error: Unable to open video file at {self.file_path}")

            width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.video_capture.release()
            return width, height

        except Exception as e:
            print(f"An error occurred while getting video dimensions: {e}")
            return None, None


if __name__ == "__main__":
    # 示例回调函数，这里仅仅打印帧的形状
    def process_frame(ret,frame):
        print(f"Frame shape: {frame.shape}")

    # 使用示例
    file_path = '../source/small_road.mp4'  # 请替换成你的实际文件路径
    video_service = VideoSrv(file_path,1000)
    print(video_service.get_video_dimensions())
    threading.Thread(target=video_service.read,args=(2500,process_frame)).start()
    # video_service.read( frame_callback=process_frame)
    time.sleep(6)
    video_service.stop()