#!/usr/bin/python3
#coding=utf8
import cv2
import os
import re
import time
import dlib
import numpy as np
import math
import threading
import getUsedSpace
import socketserver

debug = False

if debug:
    Running = True
else:
    Running = False
    
wd, hg = 640, 480
r = 19
rw, rh = int(r*4), int(r*3)

ret = False
photo_ok = False
stop = False

predictor_path = ("/home/pi/AlienbotPi/shape_predictor_5_face_landmarks.dat")
detector = dlib.get_frontal_face_detector() #获取人脸分类器
predictor = dlib.shape_predictor(predictor_path)

stream = "http://127.0.0.1:8080/?action=stream?dummy=param.mjpg"
cap = cv2.VideoCapture(stream)

Emoji_mode = 1
# 1:眼镜胡子 2：蘑菇头 3：眼镜鼻子 4： 爱心眼镜、嘴
love_mouth = cv2.imread('/home/pi/AlienbotPi/Emoji_image/love_mouth.jpg')  # 爱心嘴巴
love_glasses = cv2.imread('/home/pi/AlienbotPi/Emoji_image/love_glasses.jpg')  # 爱心眼镜
black_glasses = cv2.imread('/home/pi/AlienbotPi/Emoji_image/black_glasses.jpg')  # 黑色眼镜
goatee = cv2.imread('/home/pi/AlienbotPi/Emoji_image/goatee.jpg')  # 黑色胡子
mask = cv2.imread('/home/pi/AlienbotPi/Emoji_image/mask.jpg')  # 面具
Batman = cv2.imread('/home/pi/AlienbotPi/Emoji_image/Batman.jpg')  # 蜘蛛侠

# 读取存储图片文件夹中的文件个数
image_number = len(os.listdir("/home/pi/AlienbotPi/images"))

# 暂停信号的回调
def cv_stop():
    global Running
    print("Stop face detection")
    if Running is True:
        Running = False
    cv2.destroyWindow("face_detection")
    cv2.destroyAllWindows()
 
# 继续信号的回调
def cv_continue():
    global Running,stop
    stop = False
    if Running is False:
        Running = True
        
#数值映射
#将一个数从一个范围映射到另一个范围
def leMap(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def image_overlay(bg, logo, bg_logo_x, bg_logo_y, mask_num):
    '''
    图片叠加
    :param bg: 背景
    :param logo: 叠加在背景上的图片
    :param mask_num: 二值化低范围， 关系到logo图片是否显示全
    :return:
    '''
    # print logo.shape
    # 高度， 宽度
    try:       
        rows, cols = logo.shape[:2]
        bg_logo_x = bg_logo_x - int(cols/2)
        bg_logo_y = bg_logo_y - int(rows/2)
        if bg_logo_x < 0:
            bg_logo_x = 0
        elif bg_logo_x > 640 - cols:
            bg_logo_x = 640 - cols
        if bg_logo_y < 0:
            bg_logo_y = 0
        elif bg_logo_y > 480 - rows:
            bg_logo_y = 480 - rows
        
        y_rows = bg_logo_y + rows
        x_clos = bg_logo_x + cols
        if y_rows > 480:
            y_rows = 480
        elif y_rows < 0:
            y_rows = 0
        if x_clos > 640:
            x_clos = 640
        elif x_clos < 0:
            x_clos = 0

        roi = bg[bg_logo_y:y_rows, bg_logo_x:x_clos]
        # 创建掩膜
        img2gray = cv2.cvtColor(logo, cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(img2gray, mask_num, 255, cv2.THRESH_BINARY)        
        mask_inv = cv2.bitwise_not(mask)        
        img1_fg = cv2.bitwise_and(roi, roi, mask=mask)
        img2_fg = cv2.bitwise_and(logo, logo, mask=mask_inv)
        dst = cv2.add(img1_fg, img2_fg)      
        bg[bg_logo_y:y_rows, bg_logo_x:x_clos] = dst
    except:
        return

class ServoServer(socketserver.BaseRequestHandler):
    Flag = True
    def handle(self):
        global Emoji_mode, photo_ok,stop,Running
        print("已连接")
        conn = self.request
        recv = b''
        recv_data = ''
        while self.Flag:
            try:
                recv = conn.recv(1024)
                recv_data = recv.decode()
                if not recv_data:
                    self.Flag = False
                    print("break")
                    break
                rdata = recv_data.split("\r\n")  # 分割
                rex = re.compile(r'^(I[0-9]{3}).*')  # 判断收到的指令是否符合规则
                data = rdata[0]
                match = data
                match = rex.match(match)
                #print ("match", match)
                if match:
                    if not 0 == match.start() or not len(data) == match.end():
                        print("错误指令 1")
                    else:
                        # print 'data', data
                        data = data.split('-')
                        cmd = data[0][1:5]
                        del data[0]
                        par = []
                        cmd = int(cmd)
                        #print ('cmd', cmd)
                        for p in data:
                            par.append(p)
                        # print ('par', par)
                        if cmd == 1 and par[0] == 'connected' and par[1] == 'ok':
                            cv_continue()  # 打开摄像头窗口
                        elif cmd == 1 and par[0] == 'connected' and par[1] == 'no':
                            stop = True
                            Running = False# 关闭窗口
                        elif cmd == 2 and par[0] == 'mode':
                            #print("Emoji_mode",par[1])
                            if par[1] == '1':
                                Emoji_mode = 1
                            if par[1] == '2':
                                Emoji_mode = 2
                            if par[1] == '3':
                                Emoji_mode = 3
                            if par[1] == '4':
                                Emoji_mode = 4
                        elif cmd == 3 and par[0] == 'photo' and par[1] == 'ok':
                            photo_ok = True
                else:
                    print(data)
                    print("错误指令 2")
            except Exception as e:
                print(e)
                break

    def finish(self):
        print("已断开")

class LeServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

server = LeServer(("", 1164), ServoServer)

def get_image():
    global orgFrame
    global ret
    while True:
        if cap.isOpened():
            ret, orgFrame = cap.read()
            if not Running:
                time.sleep(0.01)               
        else:
            time.sleep(0.01)

# 显示图像线程
th1 = threading.Thread(target=get_image)
th1.setDaemon(True)  # 设置为后台线程，这里默认是False，设置为True之后则主线程不用等待子线程
th1.start()

try:
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    while True:
        if ret:
            if Running:
                ret = False
                frame = cv2.resize(orgFrame, (rw,rh), interpolation = cv2.INTER_CUBIC)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                dets = detector(gray, 1) #使用detector进行人脸检测 dets为返回的结果
                if len(dets) > 0:
                    for index, face in enumerate(dets):
                        '''
                        left = int(leMap(face.left(), 0.0, rw, 0.0, wd))
                        top  = int(leMap(face.top(), 0.0, rh, 0.0, hg))
                        right  = int(leMap(face.right(), 0.0, rw, 0.0, wd))
                        bottom = int(leMap(face.bottom(), 0.0, rh, 0.0, hg))
                        
                        cv2.rectangle(orgFrame, (left, top), (right, bottom), (0, 255, 0), 2)
                        '''
                        shape = predictor(gray, face)
                        dx = shape.parts()[0].x - shape.parts()[2].x
                        dy = shape.parts()[0].y - shape.parts()[2].y                
                        bx = leMap(shape.parts()[4].x, 0.0, rw, 0.0, wd)
                        by = leMap(shape.parts()[2].y, 0.0, rw, 0.0, wd)
                        '''
                        for i in shape.parts():
                            xx = leMap(i.x, 0.0, rw, 0.0, wd)
                            yy = leMap(i.y, 0.0, rh, 0.0, hg)
                            cv2.circle(orgFrame, (xx, yy), 5, (0, 255, 255), -1)
                        '''
                        if Emoji_mode == 1:     # 黑色眼镜框
                            w = int(1.3*leMap(shape.parts()[0].x - shape.parts()[2].x, 0.0, rw, 0.0, wd))
                            black_glass = cv2.resize(black_glasses, (w, int(w*(black_glasses.shape[0]/black_glasses.shape[1]))),interpolation = cv2.INTER_LINEAR)  # 将图片缩放
                            image_overlay(orgFrame, black_glass, bx, by, 100)
                            
                            by = leMap(shape.parts()[4].y, 0.0, rw, 0.0, wd)
                            goat = cv2.resize(goatee, (w, int(w*(goatee.shape[0]/goatee.shape[1]))),interpolation = cv2.INTER_LINEAR)  # 将图片缩放
                            image_overlay(orgFrame, goat, bx, int(by + goat.shape[0]/2), 110)
                        elif Emoji_mode == 2:   # 蝙蝠侠
                            w = int(2*leMap(dx, 0.0, rw, 0.0, wd))
                            Bat = cv2.resize(Batman, (w, int(w*(Batman.shape[0]/Batman.shape[1]))),interpolation=cv2.INTER_LINEAR)  # 将图片缩放
                            image_overlay(orgFrame, Bat, bx, int(0.75*by),220)
                        elif Emoji_mode == 3:   # 面具
                            w = int(1.5*leMap(dx, 0.0, rw, 0.0, wd))
                            ma = cv2.resize(mask, (w, int(w*(mask.shape[0]/mask.shape[1]))),interpolation=cv2.INTER_LINEAR)  # 将图片缩放
                            image_overlay(orgFrame, ma, bx, int(0.5*by),240)                            
                        elif Emoji_mode == 4:   # 爱心眼镜
                            w = int(1.5*leMap(dx, 0.0, rw, 0.0, wd))
                            love_glass = cv2.resize(love_glasses, (w, int(w*(love_glasses.shape[0]/love_glasses.shape[1]))),interpolation=cv2.INTER_LINEAR)  # 将图片缩放
                            image_overlay(orgFrame, love_glass, bx, by,100)
                            
                            dx = shape.parts()[1].x - shape.parts()[3].x
                            w = int(1.2*leMap(dx, 0.0, rw, 0.0, wd))
                            by = leMap(shape.parts()[4].y, 0.0, rw, 0.0, wd)
                            love_m = cv2.resize(love_mouth, (w, int(w*(love_mouth.shape[0]/love_mouth.shape[1]))),interpolation = cv2.INTER_LINEAR)  # 将图片缩放
                            image_overlay(orgFrame, love_m, bx, int(by + 0.6*love_m.shape[0]), 210)
                        
                if photo_ok:
                    space = getUsedSpace.getDiskSpace()
                    if space > 100.0:
                        cv2.imwrite('/home/pi/AlienbotPi/images/'+str(image_number + 1) + '.png', orgFrame)
                    photo_ok = False 
                cv2.startWindowThread()
                cv2.imshow("face_detection", orgFrame)
                cv2.waitKey(1)
                if stop:
                    print("yes")
                    cv2.destroyAllWindows()
            else:
                time.sleep(0.01)
        else:
            time.sleep(0.01)
except:
    server.shutdown()
    server.server_close()
cap.release()
cv2.destroyAllWindows()
