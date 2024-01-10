import threading
import cv2
from video_detective.video import VideoSrv
from video_detective.rtmp import RTMPSrv
import torch 
from video_detective import util
import img
import numpy as np
import json
class Item():
    def __init__(self,class_id,coordinate, xmin, ymin, xmax, ymax):
        self.class_id = class_id
        self.center_x = coordinate[0]
        self.center_y = coordinate[1]
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def __str__(self):
        # 返回一个有效的JSON格式字符串
        return json.dumps({'type_id': self.class_id, 'x': self.x ,'y': self.y})

def tensor2item(tensor) -> Item:
    # result的格式是[xmin, ymin, xmax, ymax, confidence, class]
    class_id = int(tensor[5])
    xmin, ymin, xmax, ymax = map(int, tensor[:4])
    center_coordinate = util.calculate_center(xmin, ymin, xmax, ymax)
    return Item(class_id,center_coordinate, xmin, ymin, xmax, ymax)

class DetectiveSrv():
    def __init__(self, play_srv, id, model, polygon:list=None):
        # 初始化YOLOv5模型
        self.model = model
        self.play_srv=play_srv
        self.polygon=polygon
        self.id = id

    # 在原始帧上绘制边框和中心点
    def draw_frame(self,frame, xmin, ymin, xmax, ymax, center_x, center_y, class_id):
        class_name = self.model.names.get(class_id, 'Unknown')  # 获取类别名称
        cv2.putText(frame, class_name, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)  # 显示类别名称
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)  # 绘制中心点
        cv2.putText(frame, f'({center_x}, {center_y})', (center_x, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)  # 标注中心点坐标
        # 在视频帧上绘制多边形区域
        if self.polygon is not None and len(self.polygon) > 2:
            # 定义多边形的顶点
            vertices = np.array(self.polygon, np.int32)
            vertices = vertices.reshape((-1, 1, 2))
            cv2.polylines(frame, [vertices], isClosed=True, color=(0, 255, 0), thickness=2)
            
    # 示例回调函数
    def process_frame(self,ret,frame):
        if frame is None:
            return None
        # 使用YOLOv5模型检测当前帧中的对象
        # 将BGR图像转换为RGB，因为YOLO模型需要RGB图像
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 将图像转换为模型需要的格式
        results = self.model(rgb_frame)
        # 解析结果
        results = results.xyxy[0]  # 模型返回的检测结果

        items = [tensor2item(r) for r in results if r[5] == 0]
        detected = []
        if self.polygon is not None and len(self.polygon) > 2:
            imgsrv=img.ImgPolygonSrv(None,frame,self.polygon)
            imgsrv.new_board()
        # 检测到的每个对象
        for item in items:
            if self.polygon is not None and len(self.polygon) > 2:
                #有多边形区域-检查物体的中心点是否在多边形内
                if imgsrv.is_point_in_poly((item.center_x,item.center_y)):
                    detected.append(item)
            else:#无多边形区域
                detected.append(item)
        
        # 画框
        draw_items = items
        if util.ConfigSingleton().yolo["show_detected_line"]:
            draw_items = detected
            
        for subject in draw_items:
            self.draw_frame(frame, subject.xmin, subject.ymin, subject.xmax, subject.ymax, subject.center_x, subject.center_y, subject.class_id)

        if len(detected) > 0:
            print(f"报警- id:{self.id} 区域内人数:{len(detected)}")
            detected=[]

        return frame

    def start_detect(self):
        # 人的坐标列表
        people_coordinates = []
        self.play_srv.read(frame_callback=self.process_frame)


def get_polygon_coordinates(index:int):
    # 并将列表中的列表转换为元组
    coords =  util.SafeDict(util.ConfigSingleton().detectives[index])['polygon_coordinates']
    if coords is None or len(coords) < 3:
        return None
    polygon_coordinates = [tuple(coord) for coord in coords]
    return polygon_coordinates

if __name__ == "__main__":
    # 计算合理的暂停时间
    # wait_time = int(1 / fps * 1000)

    # print("fps:",util.get_fps('../source/small_road.mp4'))
    # ds = DetectiveSrv(srv=VideoSrv(file_path,callback_interval=interval=util.ConfigSingleton().yolo["refresh_time_ms"]),polygon=[(100, 100), (200, 50), (700, 400), (450, 400)])
    # ds.detect_person()

    url = util.ConfigSingleton().detectives[1]['rtmp']["pull_stream"]
    polygon=get_polygon_coordinates(1)
    model = torch.hub.load(util.ConfigSingleton().yolo['repo_or_dir'], util.ConfigSingleton().yolo['model'])  # or yolov5n - yolov5x6, custom
    play_srv = RTMPSrv(url,stop_event=threading.Event(),cache_size=util.ConfigSingleton().pull_rtmp["cache_size"])
    ds = DetectiveSrv(play_srv=play_srv, model=model, polygon=polygon)
    ds.start_detect()