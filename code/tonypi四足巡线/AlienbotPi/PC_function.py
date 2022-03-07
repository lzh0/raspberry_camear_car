#!/usr/bin/python3
# -*- coding: UTF-8 -*-
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
**********************************************************
*******功能:所有玩法的集合，可通过不同指令进行调用********
**********************************************************
----------------------------------------------------------
Official website:http://www.lobot-robot.com/pc/index/index
Online mall:https://lobot-zone.taobao.com/
----------------------------------------------------------
以下指令均需在LX终端使用，LX终端可通过ctrl+alt+t打开，或点
击上栏的黑色LX终端图标。
----------------------------------------------------------
Usage:
  -1 | --启动颜色识别玩法
  -2 | --启动人脸检测玩法
  -3 | --启动智能巡线玩法
  -4 | --启动手指个数识别玩法
  -5 | --启动人脸个数识别玩法
  -6 | --启动二维码识别玩法
  -7 | --启动智能监控玩法
  -8 | --启动数字计算玩法
----------------------------------------------------------
Example #1:
 显示图像,识别红绿蓝三种颜色
  python3 PC_function.py -41
----------------------------------------------------------
Example #2:
  显示图像，将识别到的人脸框起来
  python3 PC_function.py -42
----------------------------------------------------------
Version: --V2.1  2019/06/03
----------------------------------------------------------
Tips:
 * 按下Ctrl+C可中断此次程序运行
----------------------------------------------------------
''')

orgFrame = None
ret = False
stream = "http://127.0.0.1:8080/?action=stream?dummy=param.mjpg"
cap = cv2.VideoCapture(stream)
width, height = 480, 360
font = cv2.FONT_HERSHEY_SIMPLEX

# 数值映射
# 将一个数从一个范围映射到另一个范围


def leMap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# 找出面积最大的轮廓
# 参数为要比较的轮廓的列表


def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # 历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300:  # 只有在面积大于300时，最大面积的轮廓才是有效的，以过滤干扰
                area_max_contour = c

    return area_max_contour, contour_area_max  # 返回最大的轮廓


def get_image():
    global orgFrame
    global ret
    global cap
    while True:
        if cap.isOpened():
            ret, orgFrame = cap.read()
        else:
            time.sleep(0.01)

#################################################
# 颜色识别


def cv_color(frame):
    global width, height
    # 颜色的字典
    color_range = {'red': [(0, 43, 46), (6, 255, 255)],
                   'blue': [(110, 43, 46), (124, 255, 255)],
                   'green': [(35, 43, 46), (77, 255, 255)],
                   }
    range_rgb = {'red': (0, 0, 255),
                 'blue': (255, 0, 0),
                 'green': (0, 255, 0),
                 }
    wd, hg = 320, 240
    dispose_frame = cv2.resize(
        frame, (wd, hg), interpolation=cv2.INTER_CUBIC)  # 将图片缩放
    gs_frame = cv2.GaussianBlur(dispose_frame, (3, 3), 0)  # 高斯模糊
    hsv = cv2.cvtColor(gs_frame, cv2.COLOR_BGR2HSV)  # 将图片转换到HSV空间

    # 分离出各个HSV通道
    h, s, v = cv2.split(hsv)
    # 直方图化
    v = cv2.equalizeHist(v)
    # 合并三个通道
    hsv = cv2.merge((h, s, v))

    color_list = []
    rad = 0
    areaMaxContour = 0
    max_area = 0
    area_max = 0
    centerX = 0
    centerY = 0

    for i in color_range:
        mask = cv2.inRange(
            hsv, color_range[i][0], color_range[i][1])  # 对原图像和掩模进行位运算
        opened = cv2.morphologyEx(
            mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))  # 开运算
        closed = cv2.morphologyEx(
            opened, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))  # 闭运算
        (image, contours, hierarchy) = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # 找出轮廓
        areaMaxContour, area_max = getAreaMaxContour(contours)  # 找出最大轮廓
        if areaMaxContour is not None:
            if area_max > max_area:  # 找最大面积
                max_area = area_max
                color_max = i
                areaMaxContour_max = areaMaxContour
    if max_area != 0:
        ((centerX, centerY), rad) = cv2.minEnclosingCircle(
            areaMaxContour_max)  # 获取最小外接圆
        # 将数据从0-160 映射到 0-480
        centerX = int(leMap(centerX, 0.0, wd, 0.0, width))
        # 将数据从0-120 映射到 0-360
        centerY = int(leMap(centerY, 0.0, hg, 0.0, height))
        rad = int(leMap(rad, 0.0, wd / 2, 0.0, 240.0))  # 将数据从0-160 映射到 0-480
        if rad >= 10:
            cv2.circle(frame, (centerX, centerY), rad, (0, 255, 0), 2)  # 画出圆心
            if color_max == 'red':  # 红色最大
                # print("red")
                SSR.thread_runActing('wag_tail', 1)
                Color_BGR = range_rgb["red"]
            elif color_max == 'green':  # 绿色最大
                SSR.thread_runActing('sit_down', 1)
                Color_BGR = range_rgb["green"]
                # print("green")
            elif color_max == 'blue':  # 蓝色最大
                SSR.thread_runActing('37', 1)
                Color_BGR = range_rgb["blue"]
                # print("blue")
        else:
            Color_BGR = (0, 0, 0)
            color_max = "Other"
    else:
        Color_BGR = (0, 0, 0)
        color_max = "None"
    cv2.putText(frame, "Color: " + color_max, (10,
                frame.shape[0] - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, Color_BGR, 2)
    return color_max
#################################################


#################################################
# 人脸检测
face_cascade = cv2.CascadeClassifier(
    '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml')
face_detection_count = 0


def face_detection(frame):
    global face_detection_count
    dispose_frame = cv2.resize(
        frame, (160, 120), interpolation=cv2.INTER_LINEAR)
    gray = cv2.cvtColor(dispose_frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 8)
    for (x, y, w, h) in faces:
        cX = int(leMap(x, 0.0, 160.0, 0.0, 480.0))  # 0-480
        cY = int(leMap(y, 0.0, 120.0, 0.0, 360.0))  # 0-360
        cW = int(leMap(w, 0.0, 160.0, 0.0, 480.0))
        cH = int(leMap(h, 0.0, 120.0, 0.0, 360.0))
        cv2.rectangle(frame, (cX, cY), (cX + cW, cY + cH), (255, 0, 0), 2)
    if len(faces) >= 1:
        face_detection_count += 1
    else:
        face_detection_count = 0
    if face_detection_count >= 5:
        # print ('hello')
        SSR.thread_runActing('36', 1)
        face_detection_count = 0
#################################################


#################################################
# 智能巡线
def turn_left_right(angle):
    '''
    左转或者右转的动作组，根据实际需要转动的角度转动，  angle 为 负数 左转 ， 正数 右转
    :param angle: 转向的角度
    :return:
    '''
    pwm = int(angle * 4.167 +
              500)  # 1000(pwm 范围) / 240(舵机角度范围) = 4.166667； 500 中位位置
    LeCmd.cmd_i001([50, 8, 1, 500, 2, 775, 3, 500, 4,
                   125, 5, 500, 6, 775, 7, 500, 8, 125])
    time.sleep(0.05)
    LeCmd.cmd_i001([50, 8, 1, pwm, 2, 775, 3, 500, 4,
                   125, 5, pwm, 6, 775, 7, 500, 8, 125])
    time.sleep(0.05)
    LeCmd.cmd_i001([50, 8, 1, pwm, 2, 875, 3, 500, 4,
                   125, 5, pwm, 6, 875, 7, 500, 8, 125])
    time.sleep(0.05)
    LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, 500, 4,
                   255, 5, 500, 6, 875, 7, 500, 8, 225])
    time.sleep(0.05)
    LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, pwm, 4,
                   255, 5, 500, 6, 875, 7, pwm, 8, 225])
    time.sleep(0.05)
    LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, pwm, 4,
                   125, 5, 500, 6, 875, 7, pwm, 8, 125])
    time.sleep(0.05)
    LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, 500, 4,
                   125, 5, 500, 6, 875, 7, 500, 8, 125])
    time.sleep(0.05)


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
                  }
    x = None
    # 高斯模糊
    gs_frame = cv2.GaussianBlur(img, (5, 5), 0)
    # 转换颜色空间
    hsv = cv2.cvtColor(gs_frame, cv2.COLOR_BGR2HSV)
    # 查找颜色
    mask = cv2.inRange(hsv, color_dist['black']
                       ['Lower'], color_dist['black']['Upper'])
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
line_th.start()


# 智能巡线
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
#################################################


#################################################
# 手指个数识别
cv_hand_last_hand_num = -1
cv_hand_two_last_hand_num = 0
cv_hand_count = 0
cv_hand_run_one = False


def cv_hand_action(hand_num):
    global cv_hand_last_hand_num, cv_hand_count, cv_hand_two_last_hand_num, cv_hand_run_one
    if hand_num == cv_hand_last_hand_num:
        cv_hand_count += 1
        if cv_hand_count >= 8:
            cv_hand_count = 0
            cv_hand_last_hand_num = -1
            if cv_hand_run_one is False:
                if hand_num == 0:
                    # print('run0')
                    SSR.thread_runActing('0', 1)
                if hand_num == 1:
                    # print('run1')
                    SSR.thread_runActing('front_back', 1)
                if hand_num == 2:
                    # print('run2')
                    SSR.thread_runActing('right_left', 1)
                if hand_num == 3:
                    # print('run3')
                    SSR.thread_runActing('rotate', 1)
                if hand_num == 4:
                    # print('run4')
                    SSR.thread_runActing('wag_tail', 1)
                if hand_num == 5:
                    # print('run5')
                    SSR.thread_runActing('37', 1)
                    cv_hand_run_one = True
                    cv_hand_two_last_hand_num = hand_num
    else:
        cv_hand_run_one = False
        cv_hand_count = 0
    cv_hand_last_hand_num = hand_num


def cv_hand_number(frame):
    binary = img_pro.image_process(frame)
    # 获取手指个数
    hand_num = img_pro.get_hand_number(binary, frame)
    # 执行相应的动作组
    if hand_num is not None:
        cv_hand_action(hand_num)
    return hand_num
#################################################


#################################################
# 人脸个数识别
def faces_number(frame):
    dispose_frame = cv2.resize(
        frame, (160, 120), interpolation=cv2.INTER_LINEAR)  # 将图片缩放到
    gray = cv2.cvtColor(dispose_frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.25, 3)
    for (x, y, w, h) in faces:
        cX = int(leMap(x, 0.0, 160.0, 0.0, 480.0))  # 将数据从0-160 映射到 0-480
        cY = int(leMap(y, 0.0, 120.0, 0.0, 360.0))  # 将数据从0-120 映射到 0-360
        cW = int(leMap(w, 0.0, 160.0, 0.0, 480.0))
        cH = int(leMap(h, 0.0, 120.0, 0.0, 360.0))
        cv2.rectangle(frame, (cX, cY), (cX + cW, cY + cH), (255, 0, 0), 2)
    cv2.putText(frame, str(len(faces)), (100, 100), font, 3, (0, 0, 255), 2)
#################################################


#################################################
# 二维码识别

def Qc_code(frame):
    global orgframe
    barcodeData = None
    min_frame = cv2.resize(
        frame, (160, 120), interpolation=cv2.INTER_LINEAR)  # 将图片缩放到
    gray_min = cv2.cvtColor(min_frame, cv2.COLOR_BGR2GRAY)
    barcodes = pyzbar.decode(gray_min)
    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        cX = int(leMap(x, 0.0, 160.0, 0.0, 480.0))  # 将数据从0-160 映射到 0-480
        cY = int(leMap(y, 0.0, 120.0, 0.0, 360.0))  # 将数据从0-120 映射到 0-360
        cW = int(leMap(w, 0.0, 160.0, 0.0, 480.0))
        cH = int(leMap(h, 0.0, 120.0, 0.0, 360.0))
        cv2.rectangle(frame, (cX,  cY), (cX + cW, cY + cH), (0, 0, 255), 2)
        barcodeData = barcode.data.decode("utf-8")
        frame_cv = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_cv)
        draw = ImageDraw.Draw(frame_pil)
        fontText = ImageFont.truetype(
            "/usr/share/fonts/chinese/simsun.ttc", 40, encoding='utf-8')
        draw.text((cX, cY - 40), barcodeData, (0, 0, 255), font=fontText)
        orgframe = cv2.cvtColor(np.asarray(frame_pil), cv2.COLOR_RGB2BGR)
    if barcodeData == 'left':
        SSR.thread_runActing('7', 6)  # 左转
    elif barcodeData == 'right':
        SSR.thread_runActing('9', 6)  # 右转
    elif barcodeData == 'straight':
        SSR.thread_runActing('1', 5)  # 直行
    elif barcodeData == 'retreat':  # 后退
        SSR.thread_runActing('4', 5)  # 后退
    else:
        pass
    return barcodeData
#################################################


#################################################
# 智能监控
# 第一帧，用于比较
moving_last_gray = None
moving_first_flag = False  # 第一帧标志位
image_number = len(os.listdir("/home/pi/AlienbotPi/video"))
four_cc = cv2.VideoWriter_fourcc(*'XVID')
out_video = cv2.VideoWriter(
    'video/' + str(image_number) + '.avi', four_cc, 20.0, (480, 360))


def moving_objiect_tracking(frame):
    global moving_last_gray, moving_first_flag
    text = "Unoccupied"
    # 转换成灰度图像
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 高斯模糊
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    if moving_first_flag and moving_last_gray is not None:
        # 计算当前帧和第一帧的不同
        cv2.accumulateWeighted(gray, moving_last_gray, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(moving_last_gray))
        # cv2.imshow('frameDelta', frameDelta)
        thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
        # 扩展阀值图像填充孔洞，然后找到阀值图像上的轮廓
        thresh = cv2.dilate(thresh, None, iterations=2)
        (_, cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        # 遍历轮廓
        for c in cnts:
            if cv2.contourArea(c) < 5000:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = "Occupied"
            moving_first_flag = False
    # 保存上一帧
    moving_last_gray = gray.copy().astype("float")
    moving_first_flag = True
    # 在当前帧上写文字以及时间戳
    cv2.putText(frame, "Monitor Status: {}".format(text), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    if text == "Occupied":
        space = getUsedSpace.getDiskSpace()
        if space > 100.0:
            out_video.write(frame)  # 如果有画面有动，录制视频
#################################################


#################################################
# 简单数字计算
last_hand_num = -1
count = 0
number_list = []
bit_count = 0
run_one = False
operator = 1    # 运算符 1：+   2：-  3： *  4：/
operator_list = ['add', 'sub', 'mul', 'div']
bit_time = 0
count_finish = False


def hand_num_action(hand_num):
    global last_hand_num, count, bit_count, run_one
    global bit_time
    if hand_num == last_hand_num:
        count += 1
        if count >= 5:  # 判断五次， 确认手指个数
            count = 0
            if count_finish is False:
                if run_one is False:    # 判断是否切换手指
                    bit_count += 1
                    number_list.append(hand_num)
                    # print number_list
                    run_one = True
                else:
                    if bit_count == 1:    # 判断第二个数是否还是一样
                        bit_time += 1   # 相同手指计时 ，1秒后，手指个数还是相同
                        if bit_time >= 8:  # 大概1.5秒
                            bit_time = 0
                            run_one = False
    else:
        run_one = False
        count = 0
        bit_time = 0
    last_hand_num = hand_num


def digital_computation(frame, key):
    global operator, count_finish, number_list, bit_count
    global last_hand_num, run_one, count, bit_time
    binary = img_pro.image_process(frame)
    # 获取手指个数
    hand_num = img_pro.get_hand_number(binary, frame)
    # 执行相应的动作组
    if hand_num is not None:
        hand_num_action(hand_num)
    else:  # 清零
        number_list = []
        bit_count = 0
        last_hand_num = -1
        run_one = False
        count = 0
        bit_time = 0
        count_finish = False
    if len(number_list) > 0:
        cv2.putText(frame, str(number_list[0]),
                    (0, 100), font, 2, (0, 0, 255), 2)
        if bit_count == 2:
            cv2.putText(frame, str(
                number_list[1]), (100, 100), font, 2, (0, 0, 255), 2)
            cv2.putText(frame, '=', (150, 100), font, 2, (0, 0, 255), 2)
            if operator == 1:
                cv2.putText(frame, '+', (50, 100), font, 2, (0, 0, 255), 2)
                cv2.putText(frame, str(
                    number_list[0] + number_list[1]), (200, 100), font, 2, (0, 0, 255), 2)
            elif operator == 2:
                cv2.putText(frame, '-', (50, 100), font, 2, (0, 0, 255), 2)
                cv2.putText(frame, str(
                    number_list[0] - number_list[1]), (200, 100), font, 2, (0, 0, 255), 2)
            elif operator == 3:
                cv2.putText(frame, '*', (50, 100), font, 2, (0, 0, 255), 2)
                cv2.putText(frame, str(
                    number_list[0] * number_list[1]), (200, 100), font, 2, (0, 0, 255), 2)
            elif operator == 4:
                if number_list[1] == 0:  # 被除数不能为0
                    cv2.putText(frame, '/', (50, 100), font, 2, (0, 0, 255), 2)
                    cv2.putText(frame, 'The dividend cannot be 0',
                                (0, 200), font, 1.1, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, '/', (50, 100), font, 2, (0, 0, 255), 2)
                    cv2.putText(frame, str(
                        number_list[0] / (number_list[1] + 0.0)), (200, 100), font, 2, (0, 0, 255), 2)
            count_finish = True
    cv2.putText(frame, operator_list[operator - 1],
                (0, 320), font, 3, (0, 0, 255), 2)
    if key == '1':
        operator = 1
    elif key == '2':
        operator = 2
    elif key == '3':
        operator = 3
    elif key == '4':
        operator = 4


#################################################
operator = 1
if len(sys.argv) > 1:  # 对传参长度进行判断
    mode = 0

    para = sys.argv[1]
    if para == "-1":
        mode = 1
    elif para == "-2":
        mode = 2
    elif para == "-3":
        mode = 3
    elif para == "-4":
        mode = 4
    elif para == "-5":
        mode = 5
    elif para == "-6":
        mode = 6
    elif para == "-7":
        mode = 7
    elif para == "-8":
        mode = 8
    else:
        print("异常：参数输入错误！")
        sys.exit()

    print('''--程序正常运行中......
          ''')

    th1 = threading.Thread(target=get_image)
    th1.setDaemon(True)
    th1.start()
    while True:
        if ret and orgFrame is not None:
            try:
                ret = False
                t1 = cv2.getTickCount()
                orgframe = cv2.resize(
                    orgFrame, (480, 360), interpolation=cv2.INTER_LINEAR)  # 将图片缩放到
                if mode == 1:
                    cv_color(orgframe)
                elif mode == 2:
                    face_detection(orgframe)
                elif mode == 3:
                    line_patrol(orgframe)
                elif mode == 4:
                    cv_hand_number(orgframe)
                elif mode == 5:
                    faces_number(orgframe)
                elif mode == 6:
                    Qc_code(orgframe)
                elif mode == 7:
                    moving_objiect_tracking(orgframe)
                elif mode == 8:
                    digital_computation(orgframe, operator)
                t2 = cv2.getTickCount()
                time_r = (t2 - t1) / cv2.getTickFrequency()
                fps = 1.0 / time_r
                cv2.putText(orgframe, "fps:" + str(int(fps)),
                            (10, orgframe.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)  # (0, 0, 255)BGR
                cv2.imshow("orgframe", orgframe)
                cv2.waitKey(1)
            except BaseException as e:
                print(e)
                continue
        else:
            time.sleep(0.01)
else:
    print("异常：请重新运行，并输入参数！")
