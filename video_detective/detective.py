import time
import cv2
from video_detective import util
import img
import numpy as np
import json
from video_detective import kafka
class Item():
    def __init__(self,class_id,coordinate, xmin, ymin, xmax, ymax,confidence, detective_id, model):
        self.class_id = class_id
        self.class_name = [v for k,v in model.names.items() if k == self.class_id][0]
        self.center_x = coordinate[0]
        self.center_y = coordinate[1]
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.confidence = confidence
        self.time = time.time()
        self.detective_id = detective_id #监控流的id

    def __str__(self):
        # 返回一个有效的JSON格式字符串
        return json.dumps({'type_id': self.class_id, 'x': self.x ,'y': self.y})

def tensor2item(tensor,detective_id,model) -> Item:
    # result的格式是[xmin, ymin, xmax, ymax, confidence, class]
    class_id = int(tensor[5])
    xmin, ymin, xmax, ymax = map(int, tensor[:4])
    center_coordinate = util.calculate_center(xmin, ymin, xmax, ymax)
    confidence = float(tensor[4])
    return Item(class_id,center_coordinate, xmin, ymin, xmax, ymax, confidence,detective_id, model)

class DetectiveSrv():
    def __init__(self, play_srv, id, models, polygon:list=None):
        # 初始化YOLOv5模型
        self.models = models
        self.play_srv=play_srv
        self.polygon=polygon
        self.id = id
        self.monitoring_topics = util.ConfigSingleton().detectives[util.ConfigSingleton().get_index_by_id(self.id)]["monitoring_topics"]

    # 在原始帧上绘制边框和中心点
    def draw_frame(self,frame, xmin, ymin, xmax, ymax, center_x, center_y, class_name):
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

        imgsrv = None
        if self.polygon is not None and len(self.polygon) > 2:
            imgsrv=img.ImgPolygonSrv(None,frame,self.polygon)
            imgsrv.new_board()

        all_detected = []
        class_ids = []
        for model in self.models:
            # 将图像转换为模型需要的格式
            results = model(rgb_frame)
            results = results.xyxy[0]  # 模型返回的检测结果
            
            items = []
            if model.names.get(0,"Unknown").lower() == "person":#模型第一个是person说明是yolov5官方模型-添加模型的“人”为监测对象
                if "person" in self.monitoring_topics:
                    items += [tensor2item(r,self.id, model) for r in results if r[5] == 0]
            else:#非官方模型-添加模型的所有类别作为监测对象
                items += [tensor2item(r,self.id, model) for r in results if r[5] in [k for k,v in model.names.items() if v in self.monitoring_topics]]
            
            detected = []
            # 检测到的每个对象
            for item in items:
                if self.polygon is not None and len(self.polygon) > 2 and item.class_id == 0 and model.names.get(0,"Unknown").lower() == "person":
                    #有多边形区域-检查人的中心点是否在多边形内
                    if imgsrv.is_point_in_poly((item.center_x,item.center_y)):
                        detected.append(item)
                else:#无多边形区域
                    detected.append(item)
            if len(detected) < 1:                    
                continue
            all_detected += detected

        # 画框
        if util.ConfigSingleton().yolo["show_detected_line"]:
            for do in all_detected:
                self.draw_frame(frame, do.xmin, do.ymin, do.xmax, do.ymax, do.center_x, do.center_y, model.names.get(do.class_id,""))

        # 报警
        if len(all_detected) > 0:
            kafka.MONITORING_ALARM_KAFKA.put(all_detected)
            all_detected=[]

        return frame

    def start_detect(self):
        self.play_srv.read(frame_callback=self.process_frame)


def get_polygon_coordinates(index:int):
    # 并将列表中的列表转换为元组
    coords =  util.SafeDict(util.ConfigSingleton().detectives[index])['polygon_coordinates']
    if coords is None or len(coords) < 3:
        return None
    polygon_coordinates = [tuple(coord) for coord in coords]
    return polygon_coordinates

if __name__ == "__main__":
    pass