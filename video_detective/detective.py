import cv2
from video import VideoSrv
import torch 
import util
import img
import numpy as np
import json

class Item():
    def __init__(self,type_id,coordinate):
        self.type_id = type_id
        self.x = coordinate[0]
        self.y = coordinate[1]

    def __str__(self):
        # 返回一个有效的JSON格式字符串
        return json.dumps({'type_id': self.type_id, 'x': self.x ,'y': self.y})

def tensor2item(tensor):
    class_id = int(tensor[5])
    xmin, ymin, xmax, ymax = map(int, tensor[:4])
    center_coordinate = util.calculate_center(xmin, ymin, xmax, ymax)
    return Item(class_id,center_coordinate)

class DetectiveSrv():
    def __init__(self,file_path=None,rtmp_url=None,interval=1000,has_part=False,polygon:list=[]):
        self.file_path = file_path
        # 初始化YOLOv5模型
        self.model = torch.hub.load(util.ConfigSingleton().yolo['repo_or_dir'], util.ConfigSingleton().yolo['model'])  # or yolov5n - yolov5x6, custom
        print("类别列表",self.model.names)
        self.classnames = self.model.names
        if file_path is not None:
            self.video_srv=VideoSrv(file_path,callback_interval=interval)
        elif rtmp_url is not None:
            self.rtmp_srv= None #TODO
        self.has_part=has_part
        self.polygon=polygon
            
    # 示例回调函数
    def process_frame(self,ret,frame):
        imgsrv=img.ImgPolygonSrv(None,frame,self.polygon)
        # 使用YOLOv5模型检测当前帧中的对象
        # 将BGR图像转换为RGB，因为YOLO模型需要RGB图像
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 将图像转换为模型需要的格式
        results = self.model(rgb_frame)

        # 解析结果
        results = results.xyxy[0]  # 模型返回的检测结果
        persons = []
        # 检测到的每个对象
        for result in results:
            # result的格式是[xmin, ymin, xmax, ymax, confidence, class]
            class_id = int(result[5])
            confidence = result[4]
            if class_id == 0:  # 数据集中的person类别的ID是0
                # 获取坐标
                xmin, ymin, xmax, ymax = map(int, result[:4])
                print(f"Detected person with confidence {confidence:.2f} at [{xmin}, {ymin}, {xmax}, {ymax}]","center point:",util.calculate_center(xmin, ymin, xmax, ymax))
                
                item = tensor2item(result)
                
                if self.has_part:#有多边形区域
                    #检查物体的中心点是否在多边形内
                    center_x, center_y = util.calculate_center(xmin, ymin, xmax, ymax)
                    if self.has_part:
                        if imgsrv.is_point_in_poly((center_x,center_y)):
                            persons.append(item)
                else:#无多边形区域
                    persons.append(item)


                # 在原始帧上绘制边框和中心点
                class_name = self.classnames.get(class_id, 'Unknown')  # 获取类别名称
                cv2.putText(frame, class_name, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)  # 显示类别名称
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)  # 绘制中心点
                cv2.putText(frame, f'({center_x}, {center_y})', (center_x, center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)  # 标注中心点坐标
                # 在视频帧上绘制多边形区域
                if self.has_part:
                    # 定义多边形的顶点
                    vertices = np.array(self.polygon, np.int32)
                    vertices = vertices.reshape((-1, 1, 2))
                    cv2.polylines(frame, [vertices], isClosed=True, color=(0, 255, 0), thickness=2)

        # 显示带有检测框的帧
        cv2.imshow('Frame', frame)

        if len(persons) > 0:
            print("报警","区域内人数：",len(persons),persons)
            persons=[]
        
        



    def detect_person(self):
        # 人的坐标列表
        people_coordinates = []
        print(self.video_srv.get_video_dimensions())
        self.video_srv.read(frame_callback=self.process_frame)



if __name__ == "__main__":
    # 计算合理的暂停时间
    # wait_time = int(1 / fps * 1000)

    print("fps:",util.get_fps('../source/small_road.mp4'))
    ds = DetectiveSrv(file_path='../source/small_road.mp4',interval=util.ConfigSingleton().yolo["refresh_time_ms"],has_part=True,polygon=[(100, 100), (200, 50), (700, 400), (450, 400)])
    ds.detect_person()

# cv2.destroyAllWindows()

# # 输出人的坐标列表
# print(people_coordinates)