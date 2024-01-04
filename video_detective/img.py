from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
import cv2

red_color = (255, 0, 0)# 红色
point_radius = 15# 设置点的半径，从而决定点的大小
line_width = 15 #线的宽度

class ImgPolygonSrv():
    def __init__(self,image_path,frame,polygon:list=None):
        # 加载图片
        if image_path is not None:
            self.image = Image.open(image_path)
        if frame is not None:
            self.image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        self.path = None
        if polygon is not None and len(polygon) > 2:
            # 定义多边形的顶点
            self.path = Path(polygon)

    def new_board(self):    
        # 创建一个可以在上面绘制的对象
        self.draw = ImageDraw.Draw(self.image)

    #显示图片
    def show(self):
        # 保存或显示图片
        self.image.show()

    # 使用matplotlib的Path类来判断点是否在多边形内
    def is_point_in_poly(self,point):
        # 设置点的颜色
        point_color = red_color  # 红色
        return self.path.contains_point(point)

    #画线
    def draw_line(self,polygon):
        # 画多边形的边
        self.draw.line(polygon + [polygon[0]], fill=red_color, width=line_width)

    #画点
    def draw_big_point(self,point):
        # 计算绘制点的边界框（一个正方形）
        left_up_point = (point[0] - point_radius, point[1] - point_radius)
        right_down_point = (point[0] + point_radius, point[1] + point_radius)

        # 使用ellipse()方法绘制一个圆来模拟点
        self.draw.ellipse([left_up_point, right_down_point], fill=red_color)

# 测试一个点
if __name__ == "__main__":
    polygon = [(100, 100), (200, 50), (2500, 100), (2150, 200), (2200, 2200)]
    ips = ImgPolygonSrv("../source/lv.png",None,polygon)
    ips.new_board()
    test_point = (2250, 1159)
    print("Point", test_point, "is in polygon:", ips.is_point_in_poly(test_point))
    
    ips.draw_line(polygon)
    ips.draw_big_point(test_point)
    ips.image.show()