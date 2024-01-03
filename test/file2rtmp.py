import cv2
import ffmpeg
import subprocess

class RTMPStreamer:
    def __init__(self, input_file, output_url):
        self.input_file = input_file
        self.output_url = output_url

    def start_stream(self):
        # Open the input video file
        cap = cv2.VideoCapture(self.input_file)
        if not cap.isOpened():
            print(f"Unable to open video file: {self.input_file}")
            return

        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Prepare the FFmpeg command for streaming
        command = [
            'ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f"{width}x{height}",
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-f', 'flv',
            self.output_url
        ]

        # Open the FFmpeg process
        process = subprocess.Popen(command, stdin=subprocess.PIPE)

        # Read the video file frame by frame and write to the FFmpeg process
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            process.stdin.write(frame.tobytes())

        # Clean up
        cap.release()
        process.stdin.close()
        process.wait()


# Usage example
#启动rtmp服务器进行测试
# docker run --rm -it -p 1935:1935 -p 1985:1985 -p 8080:8080 registry.cn-hangzhou.aliyuncs.com/ossrs/srs:5
# SRS 支持推拉多路流 参考 https://ossrs.io/lts/zh-cn/docs/v6/doc/getting-started
#OBS 添加媒体源 可以观看
if __name__ == "__main__":
    input_file = '../source/small_road.mp4'  # Replace with the path to your video file
    output_url = 'rtmp://localhost/live/livestream2'  # Replace with your RTMP server URL
    streamer = RTMPStreamer(input_file, output_url)
    streamer.start_stream()