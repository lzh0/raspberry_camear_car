import RPi.GPIO as gpio
import cv2
import time
import numpy as np
import ImageProcessing as imgproc
import FindCentrePoint as fcp



img=np.zeros((50,50,3),np.uint8)
ctrl_pin=(11,15)
ctrl_pin2=(12,16)



    
gpio.setmode(gpio.BOARD)

gpio.setup(ctrl_pin+ctrl_pin2, gpio.OUT)
gpio.setwarnings(False)#忽略警告



pwm0 = gpio.PWM(ctrl_pin[0], 1500)# 第二个参数 freq 是频率，单位为 Hz
pwm0.start(0)
pwm1 = gpio.PWM(ctrl_pin[1], 1500)
pwm1.start(0)
pwm_0 = gpio.PWM(ctrl_pin2[0], 1500)# 第二个参数 freq 是频率，单位为 Hz
pwm_0.start(0)
pwm_1 = gpio.PWM(ctrl_pin2[1], 1500)
pwm_1.start(0)



def returnCameraIndexes():
    #只检查序列号为前10的摄像头设备编号
    index=0
    arr=[]
    for i in range(10):
        cap=cv2.VideoCapture(i)
        if cap.isOpened():
            arr.append(i)
            cap.release()
    return arr

def open_camera():
    camera_device_indexes=returnCameraIndexes()
    cap = cv2.VideoCapture(camera_device_indexes[0])#使用编号0~10中第一个检测到的摄像头
    return cap
    
    

def gpio_digital_write():
    gpio.output(11, gpio.LOW)
    gpio.output(15, gpio.LOW)

def go_street(speed_precent):
    pwm0.ChangeDutyCycle(speed_precent)
    pwm1.ChangeDutyCycle(speed_precent)

    pwm_0.ChangeDutyCycle(speed_precent)
    pwm_1.ChangeDutyCycle(speed_precent)
    #time.sleep(0.5)
    #pwm0.ChangeDutyCycle(0)
    #pwm1.ChangeDutyCycle(0)
    #time.sleep(0.1)

def turn_left(speed_precent):
    pwm0.ChangeDutyCycle(0)
    pwm1.ChangeDutyCycle(speed_precent)

    #time.sleep(0.5)
    #pwm0.ChangeDutyCycle(0)
    #pwm1.ChangeDutyCycle(0)
    #time.sleep(0.1)
'''
def turn_right(speed_precent):
    pwm0.ChangeDutyCycle(speed_precent)
    pwm1.ChangeDutyCycle(0)
    #time.sleep(0.5)
    #pwm0.ChangeDutyCycle(0)
    #pwm1.ChangeDutyCycle(0)
    #time.sleep(0.1)
'''
def turn_left_back():
    pwm0.ChangeDutyCycle(speed_precent)
    pwm1.ChangeDutyCycle(0)

def turn_right_back():
def stop():
    pwm0.ChangeDutyCycle(0)
    pwm1.ChangeDutyCycle(0)


def get_keyboard_press(fd_choose,blocking:bool): #既然反正都要用到cv2.waitKey(1)，那为什么不用呢
    #存在问题！！！，感觉不如cv2.waitKey(1)，get_keyboard_press(0,Flase)情况下存在严重的键盘按键漏检、无响应等情况
    import sys,select,tty,termios#linux 命令行条件下(非)阻塞键盘按键检测
    import time
    fd_list=[sys.stdin,sys.stdin.fileno()]#sys.stdin#原版版本，都能运行，随机二选一，不同影响吧大概，待学习，#sys.stdin.fileno()#参考版本
    fd=fd_list[fd_choose]
    #仅支持读取单个按键#非阻塞按键输入检测，原版代码： https://stackoverflow.com/questions/2408560/non-blocking-console-input
    #参考版代码：https://docs.python.org/3/library/termios.html
    old_settings = termios.tcgetattr(fd)
    try:#请保留try...finally结构以保证任何情况下都能准确恢复旧的tty属性（机译），详见参考文档
        tty.setcbreak(fd)#不能删，删了就输入后就会导致阻滞，直到按下回车
        c=''#按键字符缓存空间申请
        if blocking==True:#阻塞模式
            c = sys.stdin.read(1)
                #print(c)
            
        else:#非阻塞模式
            if (select.select([fd], [], [], 0) == ([fd], [], [])):#检测是否有按键按下。如果没有这个检测会导致被阻塞直到有按键按下，即阻塞在下一句c = sys.stdin.read(1)
                c = sys.stdin.read(1)
                #print(c)
        '''
        if c == '\x1b':         # x1b is ESC    #检测按键按下ESC
            return sys.exit()#直接结束程序
        '''
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return str(c)

#if input()=='w':
def main():
    cap=open_camera()
    
    while True:
        ret, img = cap.read()
        cv2.imshow('img',img)
        #ascii--字符：char(...);字符转ascii：ord(...)
        #keyboard_press=chr(cv2.waitKey(1))#无按键按下时返回值超过了chr处理的范围，无法映射字符
        keyboard_press=cv2.waitKey(1)
        if keyboard_press==ord('w'):
            print('getchar w')
            go_street(50)
        elif keyboard_press==ord('a'):
            print('getchar a')
            turn_left(100)
        elif keyboard_press==ord('d'):
            print('getchar d')
            turn_right(100)
        elif keyboard_press==ord('s'):
            print('s')
            stop()
        elif keyboard_press==ord('q'):
            print('getchar q')
            gpio.cleanup()
            cv2.destroyAllWindows()
            break
        elif keyboard_press==ord('b'):
            while 1:
                print('getchar b')
                ret, img = cap.read()
                cv2.imshow('img',img)
                if imgproc.image_processing(img,'get_x',False)>400:#车辆偏右
                    #左转
                    turn_right(20)
                else:
                    
                    turn_left(20)
                keyboard_press=cv2.waitKey(1)
                if keyboard_press==ord('q'):
                    gpio.cleanup()
                    cv2.destroyAllWindows()
                    break

            
            
            break
        
        else:
            print('nothing')
            stop()


        '''#不如用opencv cv2.waitKey(1)....，而且非阻塞还严重漏检按键
        keyboard_press=get_keyboard_press(0,True)
        if keyboard_press==('w'):
            print('getchar w')
            go_street(50)
        elif keyboard_press==('a'):
            print('getchar a')
            turn_left(100)
        elif keyboard_press==('d'):
            print('getchar d')
            turn_right(100)
        elif keyboard_press==('s'):
            print('s')
            stop()
        elif keyboard_press==('q'):
            print('getchar q')
            gpio.cleanup(50)
            cv2.destroyAllWindows()
            break
        else:
            print('nothing')
            stop()
        '''

if __name__ == '__main__':
    main()