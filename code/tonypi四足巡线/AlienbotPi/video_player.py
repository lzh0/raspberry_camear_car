#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import cv2

path = "/home/pi/AlienbotPi/video/"
video_file = os.listdir(path)

for f in video_file:
    # 播放列表
    print (f)

while True:
    print ('1、在终端上输入q退出')
    name = input('2、请输入需要播放视频的名字，不要后缀\n')
    file_path = path + str(name) + '.avi'
    print("path-----", file_path)
    v = cv2.VideoCapture(file_path)
    while True:
        ret, frame = v.read()
        if ret:
            cv2.imshow("Playing Video", frame)
            if cv2.waitKey(1) == ord("q"):
                break
        else:
            break
    if name == 'q':
        cv2.destroyAllWindows()
        v.release()
        break
