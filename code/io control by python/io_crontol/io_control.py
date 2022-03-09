
import RPi.GPIO as gpio
import cv2
import time
import numpy as np
#import ImageProcessing as imgproc
#import FindCentrePoint as fcp


'''
#摄像头小车程序规划：
1.摄像头一个类
2.电机一个类（DC直流电机、舵机、步进电机）、【要包含控制算法嘛...?
3.图像处理一个类（也许能和摄像头类合并？
4.
'''

img=np.zeros((1,1,3),np.uint8)
img.fill(0,0,0)
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

待添加：
ctrl_end←gpio.cleanup()
'''

class MotorControl:
    motor_A=[]
    motor_B=[]
    motor_pwm=[]
    def __init__(self,motor_A_positive:int,motor_A_negative:int,motor_B_positive:int,motor_B_negative:int,motor_pwm_frequency_Hz:float):
        #import RPi.GPIO as gpio
        self.motor_A.append(motor_A_positive)
        self.motor_A.append(motor_A_negative)
        self.motor_B.append(motor_B_positive)
        self.motor_B.append(motor_B_negative)

        gpio.setmode(gpio.BOARD)
        gpio.setwarnings(False)

        gpio.setup(self.motor_A+self.motor_B, gpio.OUT)


        
        '''#待重构部分，功能：完成引脚PWM初始化及PWM控制
        #gpio.PWM(self.motorA+self.motorB,pwm_frequency_Hz)#初始化pwm 端口及频率
        #for i in range(len(self.motorA+self.motorB)):#得加数组变量
        #！！！说明：想通过把gpio类的实例塞到列表里，从而实现：以操作列表的方式访问gpio类的实例对象
        #问题：提示 实例化对象 object has no attribute 类中的函数，并且
        #可能是由于对RPI.GPIO没有正确继承导致IO操作失败....(实例化失败竟然没有提示佛了
        #暂时搁置吧...?先把巡线功能搞上线2022.03.09 14：52，能搁置个屁，只要用对象就绕不开继承，只能直接重写
        for i in self.motor_A+self.motor_B:
            self.motor_pwm.append( gpio.PWM(i,motor_pwm_frequency_Hz) )#初始化pwm 端口及频率
        '''











        def gpio_digital_write(self):   #IO口开关量控制,待完成
            gpio.output(self.motor_A+self.motor_B, gpio.LOW)#设置低电平

        def go_street(self,speed_precent):   #直走，左右侧电机同向向前
            self.motor_pwm[0].ChangeDutyCycle(0) #ChangeDutyCycle(n) 占空比调节，n为占空比# n的范围： 0.0 <= n <= 100.0
            self.motor_pwm[1].ChangeDutyCycle(speed_precent)
            self.motor_pwm[2].ChangeDutyCycle(0)
            self.motor_pwm[3].ChangeDutyCycle(speed_precent)
            

        def turn_left(self,speed_precent):#anticlockwise 顶视图下逆时针旋转，左侧电机后退，右侧电机前进
            self.motor_pwm[0].ChangeDutyCycle(0)
            self.motor_pwm[1].ChangeDutyCycle(speed_precent)
            self.motor_pwm[2].ChangeDutyCycle(speed_precent)
            self.motor_pwm[3].ChangeDutyCycle(0)
            

        def turn_right(self,speed_precent):#clockwise    顶视图下顺时针方向旋转，左侧电机前进，右侧电机后退
            self.motor_pwm[0].ChangeDutyCycle(speed_precent)
            self.motor_pwm[1].ChangeDutyCycle(0)
            self.motor_pwm[2].ChangeDutyCycle(0)
            self.motor_pwm[3].ChangeDutyCycle(speed_precent)
            

        def turn_back(self,speed_precent):
            self.motor_pwm[0].ChangeDutyCycle(speed_precent)
            self.motor_pwm[1].ChangeDutyCycle(0)
            self.motor_pwm[2].ChangeDutyCycle(speed_precent)
            self.motor_pwm[3].ChangeDutyCycle(0)

        def stop(self):
            self.motor_pwm[0].ChangeDutyCycle(0)
            self.motor_pwm[1].ChangeDutyCycle(0)
            self.motor_pwm[2].ChangeDutyCycle(0)
            self.motor_pwm[3].ChangeDutyCycle(0)



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



    

if __name__ == '__main__':
#def main():
    myMotor=MotorControl(11,15,12,16,1500)
    #cap=open_camera()
    
    while True:
        #ret, img = cap.read()
        cv2.imshow('img',img)

        #ascii--字符：char(...);字符转ascii：ord(...)
        #keyboard_press=chr(cv2.waitKey(1))#无按键按下时返回值超过了chr处理的范围，无法映射字符
        keyboard_press=cv2.waitKey(1)
        if keyboard_press==ord('w'):
            print('getchar w')
            myMotor.go_street(3)
        elif keyboard_press==ord('a'):
            print('getchar a')
            myMotor.turn_left(3)
        elif keyboard_press==ord('d'):
            print('getchar d')
            myMotor.turn_right(3)
        elif keyboard_press==ord('s'):
            print('s')
            myMotor.turn_back(3)
            
        elif keyboard_press==ord('q'):
            print('getchar q')
            gpio.cleanup()
            cv2.destroyAllWindows()
            break
        
        else:
            print('nothing')
            myMotor.stop()


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