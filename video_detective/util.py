def calculate_center(xmin, ymin, xmax, ymax):
    # 计算中心点坐标
    center_x = (xmin + xmax) // 2
    center_y = (ymin + ymax) // 2
    return center_x, center_y


# 示例使用
if __name__ == "__main__":
    xmin, ymin, xmax, ymax = 100, 150, 200, 250  # 举例目标框的坐标
    center_x, center_y = calculate_center(xmin, ymin, xmax, ymax)
    print(f"目标框的中心点坐标为 ({center_x}, {center_y})")
