import cv2
import subprocess
import sys

# 摄像头捕获设置
cap = cv2.VideoCapture(0)

# 确保摄像头已经打开
if not cap.isOpened():
    print("无法打开摄像头")
    sys.exit()

# 视频分辨率
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

# ffmpeg命令，其中包括输入和输出参数
command = [
    'ffmpeg',
    '-y',  # 覆盖输出文件
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-pix_fmt', 'bgr24',  # OpenCV的像素格式
    '-s', '{}x{}'.format(frame_width, frame_height),  # 分辨率
    '-r', '25',  # 帧率
    '-i', '-',  # 输入来自stdin
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-preset', 'ultrafast',
    '-f', 'flv',
    'rtmp://localhost/live/livestream2'
]

# 创建一个子进程给ffmpeg
process = subprocess.Popen(command, stdin=subprocess.PIPE)

while True:
    ret, frame = cap.read()
    if not ret:
        print("无法获取帧，退出")
        break

    # 写入帧数据到管道
    process.stdin.write(frame.tobytes())

    # 显示帧内容
    # cv2.imshow('Video Stream', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cap.release()
process.stdin.close()
process.wait()
cv2.destroyAllWindows()
