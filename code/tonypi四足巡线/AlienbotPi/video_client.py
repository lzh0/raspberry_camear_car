#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import cv2
import numpy as np
import time
import threading
import signal
import socket

debug = False

stream = "http://127.0.0.1:8080/?action=stream?dummy=param.mjpg"
cap = cv2.VideoCapture(stream)
orgFrame = None
Running = False
get_image_ok = False


# 暂停信号的回调
def cv_stop(signum, frame):
    global Running

    print("ball_track_Stop")
    if Running is True:
        Running = False
    cv2.destroyAllWindows()


# 继续信号的回调
def cv_continue(signum, frame):
    global stream
    global Running
    global cap
    
    if Running is False:
        cap = cv2.VideoCapture(stream)
        Running = True


#   注册信号回调
signal.signal(signal.SIGTSTP, cv_stop)
signal.signal(signal.SIGCONT, cv_continue)


def get_image():
    global Running
    global orgFrame

    while True:
        if Running:
          if cap.isOpened():
              ret, orgFrame = cap.read()
              if ret:
                  try:             
                      orgFrame = cv2.resize(orgFrame, (480,320), interpolation = cv2.INTER_CUBIC) #将图片缩放到 320*240            
                  except Exception as e:
                      print(e)
                      continue
        else:
            time.sleep(0.01)

if debug:
    Running = True
else:
    Running = False 

# 显示图像线程
th1 = threading.Thread(target=get_image)
th1.setDaemon(True)     # 设置为后台线程，这里默认是False，设置为True之后则主线程不用等待子线程
th1.start()

address = ("10.0.0.1", 8585)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(address)
sock.listen(5)
c, a = sock.accept()
frame = None

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

img = cv2.imread('02.jpg')
srcmat2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
c.send(srcmat2)
print(len(srcmat2))
# cv_continue(0, 1)
#
# while True:
#     if orgFrame is not None and get_image_ok:
#         frame = orgFrame
#         result, imgencode = cv2.imencode('.jpg', frame, encode_param)
#         data = np.array(imgencode)
#         stringData = data.tostring()
#         c.send(str(len(stringData)).ljust(16))
#         c.send(stringData)
#         get_image_ok = False
#     else:
#         time.sleep(0.01)





