import time
import os
import sys
import math
from pyzbar import pyzbar
import numpy as np
import cv2
import threading
import img_pro
import datetime
import Serial_Servo_Running as SSR
import LeCmd
import getUsedSpace
from PIL import Image, ImageDraw, ImageFont

print('''

以下指令均需在LX终端使用，LX终端可通过ctrl+alt+t打开，或点
击上栏的黑色LX终端图标。

Usage:
  -3 | --启动智能巡线玩法

Tips:
 * 按下Ctrl+C可中断此次程序运行
''')



def get_x(img):
    '''
    范围区域图像内色块的中心坐标X
    :param img:
    :return:
    '''
    # 要识别的颜色字典
    color_dist = {'red': {'Lower': np.array([0, 50, 50]), 'Upper': np.array([6, 255, 255])},
                  'blue': {'Lower': np.array([100, 80, 46]), 'Upper': np.array([124, 255, 255])},
                  'green': {'Lower': np.array([35, 43, 46]), 'Upper': np.array([77, 255, 255])},
                  'black': {'Lower': np.array([0, 0, 0]), 'Upper': np.array([180, 255, 46])},
                  'write': {'Lower': np.array([180, 255, 46]), 'Upper': np.array([255, 255, 255])},
                  }
    x = None
    # 高斯模糊
    gs_frame = cv2.GaussianBlur(img, (5, 5), 0)
    # 转换颜色空间
    hsv = cv2.cvtColor(gs_frame, cv2.COLOR_BGR2HSV)
    # 查找颜色
    mask = cv2.inRange(hsv, color_dist['write']
                       ['Lower'], color_dist['write']['Upper'])
    # 腐蚀
    mask = cv2.erode(mask, None, iterations=2)
    # 膨胀
    mask = cv2.dilate(mask, None, iterations=2)
    # 查找轮廓
    # cv2.imshow('mask', mask)
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]
    if len(cnts):
        c = max(cnts, key=cv2.contourArea)  # 找出最大的区域
        area = cv2.contourArea(c)
        # 获取最小外接矩形
        rect = cv2.minAreaRect(c)
        if area >= 500:
            xy = rect[0]
            xy = int(xy[0]), int(xy[1])
            cv2.circle(img, (xy[0], xy[1]), 3, (0, 255, 0), -1)
            x = xy[0]
            box = cv2.boxPoints(rect)
            # 数据类型转换
            box = np.int0(box)
            # 绘制轮廓
            cv2.drawContours(img, [box], 0, (0, 255, 255), 1)
    return x


# 三个区域的加权值   从上到下
line_weight = [0.1, 0.35, 0.55]
line_weight_sum = 0
for w in range(len(line_weight)):
    line_weight_sum += line_weight[w]

# 机器人应该转的角度
line_deflection_angle = 0
line_cv_ok = False
Exit_thread = False


def run_line():
    global line_cv_ok, line_deflection_angle
    while True:
        if line_cv_ok:
            if -25 <= line_deflection_angle <= 25:
                SSR.running_action_group('1', 2)
            else:
                turn_left_right(line_deflection_angle)
                time.sleep(0.15)
            line_cv_ok = False
        else:
            time.sleep(0.01)


line_th = threading.Thread(target=run_line)
line_th.setDaemon(True)     # 设置为后台线程，这里默认是False，设置为True之后则主线程不用等待子线程
if(get_x(center_frame) == 0 & & get_x(up_frame) == 0 & & get_x(down_frame) == 0){
    line_th.start()
}else{
    line_th.stop()
    '''#迷惑，这加了个啥？
    sleep(5)
    line_th.Thread(target=running_action_group, args=(actnum, times)).start()
    sleep(15)
    '''
}


def line_patrol(f):
    global line_cv_ok, line_weight, line_weight_sum, line_deflection_angle
    # 获取总图像的大小
    img_h, img_w = f.shape[:2]
    # cv2.imshow('f', f)
    up_frame = f[0:65, 0:480]
    center_frame = f[145:210, 0:480]
    down_frame = f[290:355, 0:480]
    up_x = get_x(up_frame)
    center_x = get_x(center_frame)
    down_x = get_x(down_frame)
    if up_x is not None and center_x is not None and down_x is not None and line_cv_ok is False:
        centroid_sum = up_x * \
            line_weight[0] + center_x * \
            line_weight[1] + down_x * line_weight[2]
        center_pos = (centroid_sum / line_weight_sum)  # 求出三个点的加权平均X
        deflection_angle = math.atan(
            (center_pos - (img_w / 2)) / (img_h / 2))  # 求出弧度
        line_deflection_angle = -math.degrees(deflection_angle)  # 转换成角度
        line_cv_ok = True
    elif center_x is not None and down_x is not None and line_cv_ok is False:
        centroid_sum = center_x * line_weight[1] + down_x * line_weight[2]
        # 求出三个点的加权平均X
        center_pos = (centroid_sum / (line_weight[1] + line_weight[2]))
        deflection_angle = math.atan(
            (center_pos - (img_w / 2)) / (img_h / 2))  # 求出弧度
        line_deflection_angle = -math.degrees(deflection_angle)  # 转换成角度
        line_cv_ok = True
    elif down_x is not None and line_cv_ok is False:
        centroid_sum = down_x * line_weight[2]
        center_pos = (centroid_sum / line_weight[2])  # 求出三个点的加权平均X
        deflection_angle = math.atan(
            (center_pos - (img_w / 2)) / (img_h / 2))  # 求出弧度
        line_deflection_angle = -math.degrees(deflection_angle)  # 转换成角度
        line_cv_ok = True
    else:
        line_cv_ok = False
