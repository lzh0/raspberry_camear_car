from telnetlib import NOP
import RPi.GPIO as gpio
import cv2
import time
import numpy as np
import ImageProcessing as imgproc
import FindCentrePoint as fcp


'''
#摄像头小车程序规划：
1.摄像头一个类
2.电机一个类（DC直流电机、舵机、步进电机）、【要包含控制算法嘛...?
3.图像处理一个类（也许能和摄像头类合并？
4.
'''

img=np.zeros((1,1,3),np.uint8)

ctrl_pin=[11,15]#左侧电机IO脚
ctrl_pin2=[12,16]#右侧电机IO脚

'''
#创建电机类要解决的问题：
统合IO初始化和控制：
gpio.setwarnings()
gpio.setmode()
gpio_init_setup()
pwm_init()
gpio_digital_write()
go_street()
....
stop()
'''






#rasp Pi 主板不包含硬件模数转换器ADC,所以只有数字量的输入输出
gpio.setmode(gpio.BOARD)#引脚IO编号方式选择二选一，BOARD（物理上的板子IO脚编号）和BCM（指的是 Broadcom SOC 上的通道号。您必须始终使用图表），建议BOARD，BCM可能会变动且需要查表


gpio.setwarnings(False)#忽略警告#GPIO 上可能有多个脚本/电路。如果 RPi.GPIO 检测到引脚已配置为默认值（输入）以外的内容，则在尝试配置脚本时会收到警告。要禁用这些警告：使用False

gpio.setup(ctrl_pin+ctrl_pin2, gpio.OUT)




    #可以设计通过函数创建一个列表对象，通过输入PWM引脚号自动创建并初始化PWM对象，（用list.append()

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
    
    

def gpio_digital_write():   #IO口开关量控制
    gpio.output(ctrl_pin, gpio.LOW)#设置低电平
    gpio.output(ctrl_pin2, gpio.LOW)

def go_street(speed_precent):   #直走，左右侧电机同向向前
    pwm0.ChangeDutyCycle(0) #ChangeDutyCycle(n) 占空比调节，n为占空比# n的范围： 0.0 <= n <= 100.0
    pwm1.ChangeDutyCycle(speed_precent)
    pwm_0.ChangeDutyCycle(0)
    pwm_1.ChangeDutyCycle(speed_precent)
    

def turn_left(speed_precent):#anticlockwise 顶视图下逆时针旋转，左侧电机后退，右侧电机前进
    pwm0.ChangeDutyCycle(0)
    pwm1.ChangeDutyCycle(speed_precent)
    pwm_0.ChangeDutyCycle(speed_precent)
    pwm_1.ChangeDutyCycle(0)
    

def turn_right(speed_precent):#clockwise    顶视图下顺时针方向旋转，左侧电机前进，右侧电机后退
    pwm0.ChangeDutyCycle(speed_precent)
    pwm1.ChangeDutyCycle(0)
    pwm_0.ChangeDutyCycle(0)
    pwm_1.ChangeDutyCycle(speed_precent)
    

def turn_back(speed_precent):
    pwm0.ChangeDutyCycle(speed_precent)
    pwm1.ChangeDutyCycle(0)
    pwm_0.ChangeDutyCycle(speed_precent)
    pwm_1.ChangeDutyCycle(0)
def stop():
    
    pwm0.ChangeDutyCycle(0)
    pwm1.ChangeDutyCycle(0)
    pwm_0.ChangeDutyCycle(0)
    pwm_1.ChangeDutyCycle(0)
    
    #gpio_digital_write()#nouse
    

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
            go_street(5)
        elif keyboard_press==ord('a'):
            print('getchar a')
            turn_left(5)
        elif keyboard_press==ord('d'):
            print('getchar d')
            turn_right(5)
        elif keyboard_press==ord('s'):
            print('s')
            turn_back(5)
            #stop()
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
                    turn_right(3)
                else:
                    
                    turn_left(3)
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