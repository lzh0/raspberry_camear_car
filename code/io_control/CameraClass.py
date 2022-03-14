'''
1.摄像头一个类
2.图像处理一个类（也许能和摄像头类合并？
CameraClass将要实现的功能：

'''

import cv2 
import numpy as np 
#from skimage import morphology#用于图形骨架获取

class CameraClass():
    print('import CameraClass.py successful')
    camera_VideoCapture_object_list=[]#公有类变量:相机设备对象列表，也许应该改为私有变量__camera_VideoCapture_object_list

    def __init__(self,check_camera_device_range=5): #默认只检查序列号为前5的摄像头设备编号，并对打开成功的摄像头创建实例
        self.camera_VideoCapture_object_list.clear()#清除重置，避免上次实例化时的变量数据残留
        for i in range(check_camera_device_range):
            camera_object_temp=cv2.VideoCapture(i)#尝试创建相机对象
            if camera_object_temp.isOpened():#如果成功打开设备创建了相机对象
                self.camera_VideoCapture_object_list.append(camera_object_temp)#则将对象加入到列表中
        if len(self.camera_VideoCapture_object_list)==[]: #判断是否有可用设备对象
                raise NameError('ERROR:VideoCapture(0~'+str(check_camera_device_range)+') can not find usable device, check your camera connect');raise#主动抛出异常提示信息
        else:
            print('find camera device: ',self.camera_VideoCapture_object_list)   

    def close_camera(self):
        for i in range(len(self.camera_VideoCapture_object_list)):
            self.camera_VideoCapture_object_list[i].release()#关闭摄像头对象
            cv2.destroyAllWindows()#关闭所有窗口

    def return_camera_capture_image_list(self,appoint_reading_camera_index=None,display_capture_image=True):#appoint_reading_camera_index指定读取camera_VideoCapture_object_list中的第 _变量值_ 个相机画面，若参数缺失则读取所有可用相机.
        capture_image_list=[]
        if appoint_reading_camera_index is not None:#若读取指定索引的相机
            capture_image_list.append(img_temp=((self.camera_VideoCapture_object_list[appoint_reading_camera_index]).read())[1])#读取指定相机画面，非简写见for中
        else:#参数缺失默认读取所有相机画面
            for i in range(len(self.camera_VideoCapture_object_list)):
                #ret,img=cv2.VideoCapture.read() #ret 表示捕获是否成功，成功为 True，不成功为 False; img 是返回的捕获到的帧，如果没有则为空
                #if ret=((self.camera_VideoCapture_object_list[i]).read())[0]:#是否捕获成功检测

                img_temp=((self.camera_VideoCapture_object_list[i]).read())[1]#取返回的第二个参数img，存储到函数局部变量img_temp中缓存
                capture_image_list.append(img_temp)    #使用编号0~10中第一个检测到的摄像头

        if display_capture_image==True:
            for i in range(len((capture_image_list))):
                cv2.imshow('camera_'+str(i)+' image',(capture_image_list)[i])
            cv2.waitKey(1)
            #keyboard_press=cv2.waitKey(1)#仅在显示图片时返回按键值
            #return keyboard_press
        
        return capture_image_list

    def image_processing(self,image_list=list,recognition_mode='',display_processed_imag=True,display_axis_coordinate_img=True):
        for i in image_list:
            img=i
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)#彩图转黑白灰度度，后续优化可以针对地图颜色更改RBG转灰度占比#http://www.opencv.org.cn/opencvdoc/2.3.2/html/modules/imgproc/doc/miscellaneous_transformations.html?highlight=cvtcolor#cv2.cvtColor
            gray = cv2.GaussianBlur(gray,(5,5),0,0)#高斯模糊(滤波)，该处理应在灰度前还是后，存疑
            retval, binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)# 大津法二值化，注意输出二值分别为0和255#https://zhuanlan.zhihu.com/p/95034826
            #对于白线深色的地图，去噪点选用先腐蚀再膨胀的方法；黑线白底反之。
            binary_image_pro = cv2.dilate(binary_image, None, iterations=4)#膨胀，白区域变大，最后的参数为迭代次数，腐蚀膨胀顺序与迭代次数视实际情况而定
            binary_image_sub = cv2.erode(binary_image, None, iterations=4)# 腐蚀，白区域变小
            binary_image_process_finish = cv2.dilate(binary_image_sub, None, iterations=4)# 膨胀，白区域变大

            if recognition_mode=='skeleton_extraction':
                #骨架提取模式
                a,b,skeleton=self.skeleton_extraction(binary_image_process_finish.copy())
                
            elif recognition_mode=='get_x':#区域中心点模式
                x_location=self.get_x(img,binary_image_process_finish.copy(),display_axis_coordinate_img)
                #print(x_location)
                return x_location

            else:
                print('image_processing return nothing')
                return
            

            if display_processed_imag:
                #True
                cv2.imshow('img',img)
                cv2.imshow('gray',gray)
                cv2.imshow('binary_image',binary_image)
                cv2.imshow('binary_image_sub',binary_image_sub)
                cv2.imshow('binary_image_pro',binary_image_pro)
                cv2.imshow('skeleton',skeleton)
                cv2.imshow('binary_image_process_finish',binary_image_process_finish)
                cv2.waitKey(1)
  
    #边界纵坐标取均值
    def fc_average(self,binary_image):#横行白色像素扫描，获得该行黑白边界像素坐标，并设宽度阈值的方式寻找赛道中心点
        #二值图像中0表示黑色，255表示白色
        #opencv图形为numpy矩阵数据类型，d=ndarry[a,b,c]，其中a为行坐标，b为列坐标，c为颜色通道对应BGR【OpenCV 中的默认颜色格式通常称为 RGB，但实际上是 BGR（字节反转）】,d为一个某点莫通道的像素值
        
        if (binary_image.max==0):#全0矩阵判断
            return

        size=np.shape(binary_image)#获取图像大小
        x=size[0]#尺寸获取
        y=size[1]
        #print

        #b=np.where(binary_image[int(size[0]/2)]>0)  #取图像中心点的横坐标x作为扫描行

    def skeleton_extraction(self,binary_image): #骨架提取发获得中轴线、点，使用skimage库，代价是会有毛刺
        #from skimage import morphology#用于图形骨架获取
        x=0
        y=0
        #binary_image_sub_normalization=binary_image_sub.copy()
        binary_image[binary_image>0]=1
        #高斯模糊会导致骨架提取中的毛刺增加..........amazing 

        skeleton = morphology.skeletonize(binary_image)#图形骨架提取函数仅支持输入0,1二值图像矩阵(uint8类型)，输出true,false 二值图像矩阵(Boole类型)
        
        skeleton.dtype='uint8'  #将boole类型矩阵转uint8
        skeleton[skeleton>0]=255#将0与1转为0与255二值矩阵
        #binary_image_sub[binary_image_sub>0]=255#待速度优化，可用内存换时间
        return x,y,skeleton


    #改自幻尔四足巡线代码,原版采用将画面横切三段后将每段识别到的中心点坐标按每段宽度求加权平均的方式得到当前画面识别到的中点
    #本函数目前采用单段全屏，得增加指定区域显示的功能
    def get_x(self,img,mask,display_axis_coordinate_img=True):
        '''
        范围区域图像内色块的中心坐标X
        :param img:
        :return:
        '''
        '''
        # 要识别的颜色字典
        color_dist = {'red': {'Lower': np.array([0, 50, 50]), 'Upper': np.array([6, 255, 255])},
                    'blue': {'Lower': np.array([100, 80, 46]), 'Upper': np.array([124, 255, 255])},
                    'green': {'Lower': np.array([35, 43, 46]), 'Upper': np.array([77, 255, 255])},
                    'black': {'Lower': np.array([0, 0, 0]), 'Upper': np.array([180, 255, 46])},
                    'write': {'Lower': np.array([180, 255, 46]), 'Upper': np.array([255, 255, 255])},
                    }
        x = None

        '''
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2]
        if len(cnts):
            c = max(cnts, key=cv2.contourArea)  # 找出最大的区域
            area = cv2.contourArea(c)
            # 获取最小外接矩形
            rect = cv2.minAreaRect(c)
            if area >= 500:
                xy = rect[0]
                xy = int(xy[0]), int(xy[1])
                cv2.circle(img, (xy[0], xy[1]), 3, (255, 255, 0), -1)#在中心点坐标绘制圆点
                if display_axis_coordinate_img==True:
                    cv2.imshow('get_x',img)
                
                x = xy[0]
                box = cv2.boxPoints(rect)
                # 数据类型转换
                box = np.int0(box)

                # 绘制轮廓
                cv2.drawContours(img, [box], 0, (0, 255, 255), 1)
        return x

    
'''
#测试语句，2022.03.14测试通过
my_camera=CameraClass()
img_list=my_camera.return_camera_capture_image_list()
my_camera.image_processing(image_list=img_list,recognition_mode='skeleton_extraction',display_processed_imag=True)

img=cv2.imread('E:\\road.jpg')
img_list_one=[]
img_list_one.append(img)
print(my_camera.image_processing(image_list=img_list_one,recognition_mode='get_x',display_processed_imag=True))
cv2.waitKey(0)
my_camera.close_camera()
'''



