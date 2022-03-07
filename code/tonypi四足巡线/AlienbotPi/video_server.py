#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import cv2
import numpy as np
import time
import urllib
import threading
import socket
import servo_thread_running as STR
import os
import PC_function as PCF

parent, child = socket.socketpair()
pid = os.fork()
if pid:
    stream = "http://127.0.0.1:8080/?action=stream?dummy=param.mjpg"
    orgFrame = None
    Running = False
    get_image_ok = False
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
    functionNum = -1
    operator = 1  # 运算符 1：+   2：-  3： *  4：/

    # 继续信号的回调
    def cv_continue(signum, frame):
        global stream
        global Running
        global cap
        
        if Running is False:
            cap = cv2.VideoCapture(stream)
            Running = True

    def get_image():
        global Running
        global orgFrame
        global get_image_ok
        global cap
        
        while True:
            if Running:
              if cap.isOpened():
                  ret, orgFrame = cap.read()
                  if ret:
                      try:             
                          orgFrame = cv2.resize(orgFrame, (480,360), interpolation = cv2.INTER_CUBIC) #将图片缩放到 320*240
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

    def send_image(sock, image):
        global client_socket
        result, imgencode = cv2.imencode('.jpg', image, encode_param)
        data = np.array(imgencode)
        stringData = data.tostring()
        str_size = 'image-' + str(len(stringData))
        sock.sendall(bytes(str_size, encoding='utf-8').ljust(16))
        sock.sendall(stringData)

    def send_function_data(s, n_str):
        # 1、发送 识别符 - 数据大小
        str_bur = 'function-' + str(len(n_str))
        s.sendall(bytes(str_bur, encoding='utf-8').ljust(16))
        # 2、发送数据
        s.sendall(bytes(n_str,encoding='utf-8'))

    # 接收函数
    def recvall(s, count):
        buf = b''
        while count:
            newbuf = s.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def process_socket_recv_cmd():
        global functionNum, operator
        while True:
            buf_size = recvall(parent, 16).decode()
            # 2、接收数据
            buf = recvall(parent, int(buf_size)).decode()
            # 3、判断接收到的数据和发送来的数据大小是否相等
            if len(buf) == int(buf_size) and  buf is not None:
                buf_list = buf.split('-')
                if buf_list[1] == '4':
                    operator = buf_list[2]
                functionNum = int(buf_list[1])

    th2 = threading.Thread(target=process_socket_recv_cmd)
    th2.setDaemon(True)
    th2.start()

    last_data = False
    send_num = 0
    # 开启接收摄像头图像
    cv_continue(0, 1)
    while True:
        try:
            if orgFrame is not None and get_image_ok:
                frame = orgFrame
                # 1：Color  2：Face  3：FaceNumber  4：Digital  5：HandNumber
                # 6：LinePatrol 7：Monitor  8：QcCode
                if functionNum == 1:
                    color = PCF.cv_color(frame)
                    if color is not None and last_data != color and send_num == 0:
                        s_str = 'FunctionData-1-' + color
                        send_function_data(parent, s_str)
                        send_num += 1
                    else:
                        send_num = 0
                    last_data = color
                elif functionNum == 2:
                    PCF.face_detection(frame)
                elif functionNum == 3:
                    PCF.faces_number(frame)
                elif functionNum == 4:
                    PCF.digital_computation(frame, operator)
                elif functionNum == 5:
                    try:
                        h_number = PCF.cv_hand_number(frame)
                        if h_number is not None and last_data != h_number and send_num == 0:
                            s_str = 'FunctionData-5-' + str(h_number)
                            send_function_data(parent, s_str)
                            send_num += 1
                        else:
                            send_num = 0
                        last_data = h_number
                    except Exception as e:
                        print (e)
                elif functionNum == 6:
                    PCF.line_patrol(frame)
                elif functionNum == 7:
                    PCF.moving_objiect_tracking(frame)
                elif functionNum == 8:
                    QR = PCF.Qc_code(frame)
                    if QR is not None and last_data != QR and send_num == 0:
                        try:
                            for ch in QR:
                                if '\u4e00' <= ch <= '\u9fff':
                                    s_str = 'FunctionData-8-' + 'NonCharacter'
                                else:
                                    s_str = 'FunctionData-8-' + str(QR)
                                send_function_data(parent, s_str)
                                send_num += 1
                        except:
                            pass
                    else:
                        send_num = 0
                    last_data = QR
                send_image(parent, frame)
                get_image_ok = False
            else:
                time.sleep(0.01)
        except Exception as e:
            parent.shutdown()
            print ('parent error')
            break

else:
    address = ("", 1989)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定ip, 端口
    sock.bind(address)
    # 监听客户端个数
    sock.listen(5)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
    # 开始动作组运行线程(包含两条线程，1、串口发送   2、动作组运行)
    STR.start_action_thread()

    client_socket = None
    client_close_flag = False
    frame = None

    # 接收函数
    def recvall(s, count):
        buf = b''
        while count:
            newbuf = s.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def process_socket_seed_str(s, n_str):
        s.sendall(bytes(str(len(n_str)).ljust(16), encoding='utf-8'))
        s.sendall(bytes(n_str, encoding='utf-8'))

    def threading_recv():
        global client_close_flag, client_socket, functionNum
        while True:
            try:
                if client_socket is not None and client_close_flag is False:
                    # 1、先接收数据大小
                    buf_size = recvall(client_socket, 16).decode()
                    # 2、接收数据
                    buf = recvall(client_socket, int(buf_size)).decode()
                    # 3、判断接收到的数据和发送来的数据大小是否相等
                    if len(buf) == int(buf_size) and buf is not None:
                        # 相等有效
                        print ('buf',buf)                        
                        buf_list = buf.split('-')
                        if buf_list[0] == 'cmd':
                            if buf_list[1] == 'runAction':  # 运行动作组
                                print (buf_list[2:])
                                if buf_list[2] == 'diy':    # 运行输入名称动作组
                                    # 停止当前运行动作
                                    STR.stop_action_group()
                                    STR.change_action_value(buf_list[3], int(buf_list[4]))
                                elif buf_list[2] == 'stop':
                                    STR.stop_action_group()
                                else:
                                    STR.change_action_value(buf_list[2], int(buf_list[3]))
                            elif buf_list[1] == 'runFunction':  # 运行玩法
                                # 1：Color  2：Face  3：FaceNumber  4：Digital  5：HandNumber
                                # 6：LinePatrol 7：Monitor  8：QcCode
                                if buf_list[2] == '1':
                                    process_socket_seed_str(child, 'function-1')
                                elif buf_list[2] == '2':
                                    process_socket_seed_str(child, 'function-2')
                                elif buf_list[2] == '3':
                                    process_socket_seed_str(child, 'function-3')
                                elif buf_list[2] == '4':
                                    process_socket_seed_str(child, 'function-4-' + buf_list[3])
                                elif buf_list[2] == '5':
                                    process_socket_seed_str(child, 'function-5')
                                elif buf_list[2] == '6':
                                    process_socket_seed_str(child, 'function-6')
                                elif buf_list[2] == '7':
                                    process_socket_seed_str(child, 'function-7')
                                elif buf_list[2] == '8':
                                    process_socket_seed_str(child, 'function-8')
                                elif buf_list[2] == 'stop':
                                    process_socket_seed_str(child, 'function-0')

                        # 客户端退出
                        if buf == 'client close':
                            client_close_flag = True
                else:
                    time.sleep(0.01)
            except:
                time.sleep(0.01)


    th2 = threading.Thread(target=threading_recv)
    # 精灵线程，主线程退出，侧退出
    th2.setDaemon(True)
    th2.start()


    def send_image(s, image):
        str_size = 'image-' + str(len(image))
        s.sendall(bytes(str_size, encoding='utf-8').ljust(16))
        s.sendall(image)

    def send_function_data(s, n_str):
        # 1、发送 识别符 - 数据大小
        str_bur = 'function-' + str(len(n_str))
        s.sendall(bytes(str_bur, encoding='utf-8').ljust(16))
        # 2、发送数据
        s.sendall(n_str)


    while True:
        try:
            # 获取套接字
            client_socket, a = sock.accept()
            client_socket.settimeout(5)
            print (client_socket, a)
            while True:
                try:
                    imgsize = recvall(child, 16).decode()
                    size_list = imgsize.split('-')
                    if size_list[0] == 'image':
                        frameData = recvall(child, int(size_list[1]))
                        if frameData is not None:
                            send_image(client_socket, frameData)
                    elif size_list[0] == 'function':
                        function_data = recvall(child, int(size_list[1]))
                        send_function_data(client_socket, function_data)
                    if client_close_flag:
                        client_close_flag = False
                        client_socket.close()
                        client_socket = None
                        break
                    else:
                        time.sleep(0.01)
                except:
                    client_close_flag = False
                    client_socket.close()
                    client_socket = None
                    break
        except:
            print ('child error')
            child.shutdown()
            client_socket.shutdown()
            break
    client_socket.shutdown()
