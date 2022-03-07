#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# 小球追踪，x

import cv2
import numpy as np
import time
import urllib
import threading
import signal
import pid
import LeCmd
import Serial_Servo_Running as SSR

stream = None
bytes = ''
orgFrame = None
Running = False
get_image_ok = False
dis_ok = False
ball_x = 0
ball_size = 0

go_pid = pid.PID(P=9.6, I=0.0, D=0.0)
turn_lr_pid = pid.PID(P=3.1, I=0.0, D=0.1)
turn_out_pwm = 0
move_back_pwm = 0


# 暂停信号的回调
def cv_stop(signum, frame):
    global Running

    print("ball_track_Stop")
    if Running is True:
        Running = False
    cv2.destroyWindow('ball_track')
    cv2.destroyAllWindows()


# 继续信号的回调
def cv_continue(signum, frame):
    global stream
    global Running

    print("小球跟踪")
    if Running is False:
        # 开关一下连接
        if stream:
            stream.close()
        stream = urllib.urlopen("http://127.0.0.1:8080/?action=stream?dummy=param.mjpg")
        bytes = ''
        Running = True


#   注册信号回调
signal.signal(signal.SIGTSTP, cv_stop)
signal.signal(signal.SIGCONT, cv_continue)


def get_image():
    global Running
    global orgFrame
    global bytes
    global get_image_ok
    while True:
        if Running:
            try:
                bytes += stream.read(2048)  # 接收数据
                a = bytes.find('\xff\xd8')  # 找到帧头
                b = bytes.find('\xff\xd9')  # 找到帧尾
                if a != -1 and b != -1:
                    jpg = bytes[a:b + 2]  # 取出图片数据
                    bytes = bytes[b + 2:]  # 去除已经取出的数据
                    orgFrame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR)  # 对图片进行解码
                    orgFrame = cv2.resize(orgFrame, (480, 360), interpolation=cv2.INTER_LINEAR)  # 将图片缩放到\
                    get_image_ok = True
            except Exception as e:
                print(e)
                continue
        else:
            time.sleep(0.01)


# 显示图像线程
th1 = threading.Thread(target=get_image)
th1.setDaemon(True)     # 设置为后台线程，这里默认是False，设置为True之后则主线程不用等待子线程
th1.start()


def move_back(pwm):
    '''

    :param pwm: 前进后退pwm， 正前进， 负后退
    :return:
    '''
    if -20 <= pwm <= 20:
        LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, 500, 4, 125, 5, 500, 6, 875, 7, 500, 8, 125])
        time.sleep(0.05)
    else:
        pwm = 500 - pwm
        LeCmd.cmd_i001([100, 8, 1, 500, 2, 775, 3, 500, 4, 125, 5, 500, 6, 775, 7, 500, 8, 125])
        time.sleep(0.1)
        LeCmd.cmd_i001([100, 8, 1, pwm, 2, 775, 3, 500, 4, 125, 5, 1000-pwm, 6, 775, 7, 500, 8, 125])
        time.sleep(0.1)
        LeCmd.cmd_i001([50, 8, 1, pwm, 2, 875, 3, 500, 4, 125, 5, 1000-pwm, 6, 875, 7, 500, 8, 125])
        time.sleep(0.05)
        LeCmd.cmd_i001([100, 8, 1, 500, 2, 875, 3, 500, 4, 225, 5, 500, 6, 875, 7, 500, 8, 225])
        time.sleep(0.1)
        LeCmd.cmd_i001([100, 8, 1, 500, 2, 875, 3, pwm, 4, 225, 5, 500, 6, 875, 7, 1000-pwm, 8, 225])
        time.sleep(0.1)
        LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, pwm, 4, 125, 5, 500, 6, 875, 7, 1000-pwm, 8, 125])
        time.sleep(0.05)


def turn_left_right(pwm):
    '''

    :param pwm: 左右转的转动幅度， 负数为l 转， 正数为 r转
    :return:
    '''
    if -60 <= pwm <= 60:
        LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, 500, 4, 125, 5, 500, 6, 875, 7, 500, 8, 125])
        time.sleep(0.05)
    else:
        pwm = 500 - pwm
        LeCmd.cmd_i001([100, 8, 1, 500, 2, 775, 3, 500, 4, 125, 5, 500, 6, 775, 7, 500, 8, 125])
        time.sleep(0.1)
        LeCmd.cmd_i001([100, 8, 1, pwm, 2, 775, 3, 500, 4, 125, 5, pwm, 6, 775, 7, 500, 8, 125])
        time.sleep(0.1)
        LeCmd.cmd_i001([50, 8, 1, pwm, 2, 875, 3, 500, 4, 125, 5, pwm, 6, 875, 7, 500, 8, 125])
        time.sleep(0.05)
        LeCmd.cmd_i001([100, 8, 1, 500, 2, 875, 3, 500, 4, 225, 5, 500, 6, 875, 7, 500, 8, 225])
        time.sleep(0.1)
        LeCmd.cmd_i001([100, 8, 1, 500, 2, 875, 3, pwm, 4, 225, 5, 500, 6, 875, 7, pwm, 8, 225])
        time.sleep(0.1)
        LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, pwm, 4, 125, 5, 500, 6, 875, 7, pwm, 8, 125])
        time.sleep(0.05)
        LeCmd.cmd_i001([50, 8, 1, 500, 2, 875, 3, 500, 4, 125, 5, 500, 6, 875, 7, 500, 8, 125])
        time.sleep(0.05)


def run_action():
    global dis_ok
    global turn_out_pwm
    global move_back_pwm
    while True:
        if dis_ok is True:
            move_back(move_back_pwm)
            turn_left_right(turn_out_pwm)
            dis_ok = False
        else:
            time.sleep(0.01)


# 启动动作在运行线程
th2 = threading.Thread(target=run_action)
th2.setDaemon(True)
th2.start()


# 要识别的颜色字典
color_dist = {'red': {'Lower': np.array([0, 60, 60]), 'Upper': np.array([6, 255, 255])},
              'blue': {'Lower': np.array([100, 80, 46]), 'Upper': np.array([124, 255, 255])},
              'green': {'Lower': np.array([35, 43, 46]), 'Upper': np.array([77, 255, 255])},
              }
# PS中的HSV范围，H是0-360，S是0-1，V（B）是0-1
# opencv中的HSV范围，H是0-180，S是0-255，V是0-255
# 青色颜色  48,112,216
# 把PS中H的值除以2，S乘255，V乘255，可以得到对应的opencv的HSV值
# cyan_rect = {'Lower': np.array([18, 72, 186]),
#              'Upper': np.array([78, 142, 246])}

cv_continue(0, 0)
SSR.running_action_group('0', 1)
while True:
    if orgFrame is not None and get_image_ok:
        t1 = cv2.getTickCount()
        frame = cv2.flip(orgFrame, 1)
        min_frame = cv2.resize(frame, (160, 120), interpolation=cv2.INTER_LINEAR)
        img_h, img_w = min_frame.shape[:2]
        img_center_x = img_w / 2
        img_center_y = img_h / 2
        # print(img_center_x, img_center_y)
        # 高斯模糊
        gs_frame = cv2.GaussianBlur(min_frame, (5, 5), 0)
        # 转换颜色空间
        hsv = cv2.cvtColor(gs_frame, cv2.COLOR_BGR2HSV)
        # 查找颜色
        mask = cv2.inRange(hsv, color_dist['green']['Lower'], color_dist['green']['Upper'])
        # 腐蚀
        mask = cv2.erode(mask, None, iterations=2)
        # 膨胀
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        # 查找轮廓
        # cv2.imshow('mask', mask)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = None
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            # 求出最小外接圆  原点坐标x, y  和半径
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            if radius >= 7:  #
                cv2.circle(frame, (int(x * 3), int(y * 3)), int(radius * 3), (0, 0, 255), 2)
                cv2.circle(frame, (int(x * 3), int(y * 3)), 5, (0, 0, 255), -1)
                # print(x, y, radius)
                # 获取小球x轴位置
                ball_x = int(x)
                # 获取小球半径
                ball_size = int(radius)
                # 设置要保持的点的位置
                turn_lr_pid.SetPoint = img_center_x
                # 更新x轴位置
                turn_lr_pid.update(ball_x)
                # pid输出
                turn_out_pwm = turn_lr_pid.output
                # 整型
                turn_out_pwm = int(turn_out_pwm)
                if turn_out_pwm > 500:
                    turn_out_pwm = 500
                elif turn_out_pwm < -500:
                    turn_out_pwm = -500
                ###########################################
                go_pid.SetPoint = 28
                go_pid.update(60 - ball_size)   # 小球最大半径60
                move_back_pwm = go_pid.output
                move_back_pwm = -int(move_back_pwm)
                if move_back_pwm > 500:
                    move_back_pwm = 500
                elif move_back_pwm < -500:
                    move_back_pwm = -500
                # print turn_out_pwm
                # print move_back_pwm
                # print 'ball', ball_size
                dis_ok = True
                # 设置要保持的点的位置
        # 参数：图片, 起点, 终点, 颜色, 粗细
        cv2.namedWindow("ball_track", cv2.WINDOW_AUTOSIZE)
        cv2.imshow('ball_track', frame)
        cv2.waitKey(1)
        get_image_ok = False
        t2 = cv2.getTickCount()
        time_r = (t2 - t1) / cv2.getTickFrequency() * 1000
        # print("%sms" % time_r)
    else:
        time.sleep(0.01)


