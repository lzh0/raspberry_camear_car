
from curses import flash
import RPi.GPIO as gpio
import cv2
import time
import numpy as np#用于创建空白图像
from CameraClass import *#引入自制相机类


'''
#摄像头小车程序规划：
1.摄像头一个类(含图像处理获得中轴线坐标)：CameraClass【待完善类初始化时的相机设置】
2.
3.电机驱动一个类（DC直流电机√、舵机、步进电机）、...?
4.电机控制一个类
5.控制算法一个类（先上个PID
6.巡线运行一个类

'''

class MotorDrive:   #电机驱动类，实现电机驱动初始化
    #motor_io_list=[]#不要在类方法之外定义声明变量，变量会无法被清除重置，导致影响下次类实例化
    
    def __init__(self,gpio_setmode=gpio.BOARD, gpio_setwarnings=False, digital_io_list=[],pwm_io_list=[],motor_pwm_frequency_Hz=1500):#使用默认值时，必须先在形参列表中列出没有默认值的形参，再列出有默认值的实参。这让Python依然能够正确地解读位置实参。
        self.motor_pwm_object_list=[]
        gpio.setmode(gpio_setmode)
        gpio.setwarnings(gpio_setwarnings)
        gpio.setup(digital_io_list+pwm_io_list, gpio.OUT)
        
        if not digital_io_list==[]:  #电机驱动数字端口电平状态控制
            #IO口开关量控制,待完成   #需要前置语句import RPI.GPIO as gpio, gpio.setmode(),gpio.setup(),gpio.setwarnings()【可选】
            gpio.output(digital_io_list[0],gpio.LOW)#设置低电平
            gpio.output(digital_io_list[1],gpio.HIGH)#设置高电平
        #如果电机依靠IO口电平状态控制正反转代码：
        #...【待完成】
        
        if pwm_io_list==[]: 
            raise NameError('ERROR:pwm_io_list is empty');raise#主动抛出异常提示信息
        else:   #pwm端口对象实例化
            for io_num in pwm_io_list:
                self.motor_pwm_object_list.append(gpio.PWM(io_num,motor_pwm_frequency_Hz) )#初始化pwm 端口及频率
                self.motor_pwm_object_list[len(self.motor_pwm_object_list)-1].start(0)  #打开并开始端口的PWM实例输出控制

    def change_motor_speed(self,speed_vale_negative_100_0_to_positive_100_0:float):#speed_vale_negative_100_0_to_positive_100_0的范围： 0.0 <= n <= 100.0
        if speed_vale_negative_100_0_to_positive_100_0<0:   #输入负数反转
            speed_vale_negative_100_0_to_positive_100_0=abs(speed_vale_negative_100_0_to_positive_100_0)#取绝对值，从另一个PWM通道输出
            self.motor_pwm_object_list[0].ChangeDutyCycle(speed_vale_negative_100_0_to_positive_100_0)#ChangeDutyCycle(n) 占空比调节，n为占空比# n的范围： 0.0 <= n <= 100.0
            self.motor_pwm_object_list[1].ChangeDutyCycle(0)
        else:
            
            self.motor_pwm_object_list[0].ChangeDutyCycle(0)
            self.motor_pwm_object_list[1].ChangeDutyCycle(speed_vale_negative_100_0_to_positive_100_0)


class MotorControl: ##电机控制类，待完成差速运行、差速转弯等
    '''
    ↑ go_straight() ↑
wheel_A0|——————|wheel_B0
  motorA| car  |motorB
wheel_A1|——————|wheel_B1
    车辆电机位置示意图：
    '''

    def __init__(self,motor_A_digital_io_list=[],motor_A_pwm_io_list=[],motor_B_digital_io_list=[],motor_B_pwm_io_list=[],motor_pwm_frequency_Hz=1500,delay_time_s_=0.3):
        #super().__init__(digital_io_list=motor_A_digital_io_list+motor_A_pwm_io_list,pwm_io_list=motor_B_digital_io_list+motor_pwm_frequency_Hz)#继承MotorDrive类
        #赶紧还是用实例化好一点吧大概
        self.delay_time_s=delay_time_s_
        self.motor_A=MotorDrive(digital_io_list=motor_A_digital_io_list, pwm_io_list=motor_A_pwm_io_list, motor_pwm_frequency_Hz=motor_pwm_frequency_Hz)
        self.motor_B=MotorDrive(digital_io_list=motor_B_digital_io_list, pwm_io_list=motor_B_pwm_io_list, motor_pwm_frequency_Hz=motor_pwm_frequency_Hz)

    def  motor_A_B_speed_set(self,speed_vale_A,speed_vale_B):
        self.motor_A.change_motor_speed(speed_vale_A)
        self.motor_B.change_motor_speed(speed_vale_B)
        time.sleep(self.delay_time_s)
        
    def go_straight(self,speed_vale):   #直走，左右侧电机同向向前
        self.motor_A_B_speed_set(speed_vale_A=-speed_vale,speed_vale_B=-speed_vale)
        time.sleep(self.delay_time_s)

    def turn_left(self,speed_vale):#anticlockwise 顶视图下逆时针旋转，左侧电机后退，右侧电机前进
        self.motor_A_B_speed_set(speed_vale_A=speed_vale,speed_vale_B=-speed_vale)
        time.sleep(self.delay_time_s)

    def turn_right(self,speed_vale):#clockwise    顶视图下顺时针方向旋转，左侧电机前进，右侧电机后退
        self.motor_A_B_speed_set(speed_vale_A=-speed_vale,speed_vale_B=speed_vale)
        time.sleep(self.delay_time_s)

    def turn_back(self,speed_vale):
        self.motor_A_B_speed_set(speed_vale_A=speed_vale,speed_vale_B=speed_vale)
        time.sleep(self.delay_time_s)

    def stop(self):
        self.motor_A_B_speed_set(speed_vale_A=0.0,speed_vale_B=0.0)
 
#巡线运行类，待完成
class FollowLine:#需要对电机的控制√MotorControl()，需要当前赛道的中轴x坐标，需要PID巡线算法加持
    
    
    def __init__(self,motor_AB_control_object:object,my_camera:object,camera_image_size_x=int,motor_max_speed=5.0):
        self.__motor_AB_control_object=motor_AB_control_object
        self.__my_camera=my_camera
        self.__camera_image_size_x=camera_image_size_x#后期优化一下自动获取相机参数
        self.__motor_max_speed=motor_max_speed
        
    def return_error_precent(self):
        self.__mycamera_image_list=self.__my_camera.return_camera_capture_image_list(display_capture_image=False)#未指定相机【待优化appoint_reading_camera_index=0】，显示图片
        self.__road_x=self.__my_camera.image_processing(image_list=self.__mycamera_image_list,recognition_mode='get_x',display_processed_imag=False,display_axis_coordinate_img=True)
        self.__camera_axis_coordinate_x=self.__camera_image_size_x/2
        #偏差值=赛道中轴坐标x-(相机屏幕x大小/2，即相机画幅中轴x坐标)
        self.__error=self.__road_x-self.__camera_axis_coordinate_x
        
        if -1e-7<self.__error<1e-7:  #判断误差是否为0，浮点数判断不能用self.__error==0:会有误差，只能取近似逼近
            self.__error_precent=0.0
        else:
        #偏差率=当前偏差值/总偏差值
            self.__error_precent=((self.__camera_axis_coordinate_x)/(self.__error))
        #偏差率<0则车体偏左，应向右转，反之若偏差率>0则车体偏右，应向左转
 
        return self.__error_precent

    def follow_line_simple(self,):#测试成功，通过20220314，18:57,处理速度跟不上电机最低转速...
        
        while 1:
            self.__mycamera_image_list=self.__my_camera.return_camera_capture_image_list(display_capture_image=False)#未指定相机【待优化appoint_reading_camera_index=0】，显示图片
            road_x=self.__my_camera.image_processing(image_list=self.__mycamera_image_list,recognition_mode='get_x',display_processed_imag=False)
            if road_x>(self.__camera_image_size_x)/2:#车辆偏右
                #turn_left(3)#左转
                self.__motor_AB_control_object.motor_A_B_speed_set(-0.1,0)
                print('tturn_left',self.return_error_precent())
            else:#车辆偏左
                #turn_right(3)#右转
                self.__motor_AB_control_object.motor_A_B_speed_set(0,-0.1)
                print('turn_righ',self.return_error_precent())

            keyboard_press=cv2.waitKey(1)
            print('self.__road_x: ',self.__road_x)
            if keyboard_press==ord('q'):
                gpio.cleanup()
                cv2.destroyAllWindows()
                break

    def follow_line_by_PID(self):
        error_precent=self.return_error_precent()
        self.__motor_AB_control_object.motor_A_B_speed_set(-0.1,0)



def keyboard_control_car(img,motor_AB_control_object:object,every_step_delay_time_s:float):
    myMotor=motor_AB_control_object
    while True:
        #ret, img = cap.read()
        cv2.imshow('img',img)

        #ascii--字符：char(...);字符转ascii：ord(...)
        #keyboard_press=chr(cv2.waitKey(1))#无按键按下时返回值超过了chr处理的范围，无法映射字符
        keyboard_press=cv2.waitKey(1)
        if keyboard_press==ord('w'):
            print('getchar w')
            myMotor.go_straight(3.0)
            

        elif keyboard_press==ord('a'):
            print('getchar a')
            myMotor.turn_left(3.0)
            

        elif keyboard_press==ord('d'):
            print('getchar d')
            myMotor.turn_right(3.0)
            
            
        elif keyboard_press==ord('s'):
            print('s')
            myMotor.turn_back(3.0)
            
        elif keyboard_press==ord('q'):
            print('getchar q')
            gpio.cleanup()
            cv2.destroyAllWindows()
            break
        elif keyboard_press==ord('f'):
            #follow_line()
            print('into follow line model in __main__')
            cv2.destroyAllWindows()
            break
        else:
            print('nothing')
            myMotor.stop()


if __name__ == '__main__':
    img=np.zeros((1,1,3),np.uint8)
    img.fill(255)
#def main():
    '''
    MotorDrive类测试
    motorAtest=MotorDrive(pwm_io_list=[11,15])
    motorAtest.change_motor_speed(3)
    time.sleep(1)
    motorAtest.change_motor_speed(-3)
    time.sleep(1)

    motorBtest= MotorDrive(pwm_io_list=[12,16])
    motorBtest.change_motor_speed(3)
    time.sleep(1)
    motorBtest.change_motor_speed(-3)
    time.sleep(1)
    '''
    myMotor=MotorControl(motor_A_pwm_io_list=[11,15],motor_B_pwm_io_list=[12,16],motor_pwm_frequency_Hz=1500)
    #cap=open_camera()
    keyboard_control_car(img,motor_AB_control_object=myMotor,every_step_delay_time_s=0.5)

    mycamera=CameraClass()
    myfollow_line=FollowLine(motor_AB_control_object=myMotor,my_camera=mycamera,camera_image_size_x=640)
    myfollow_line.follow_line_simple()

    gpio.cleanup()
    cv2.destroyAllWindows()
    
    

