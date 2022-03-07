import numpy as np 

import cv2
def import_successful():
    print('import FindCentrePoint.py successful')
    return

#边界纵坐标取均值
def fc_average(binary_image):#横行白色像素扫描，获得该行黑白边界像素坐标，并设宽度阈值的方式寻找赛道中心点
    #二值图像中0表示黑色，255表示白色
    #opencv图形为numpy矩阵数据类型，d=ndarry[a,b,c]，其中a为行坐标，b为列坐标，c为颜色通道对应BGR【OpenCV 中的默认颜色格式通常称为 RGB，但实际上是 BGR（字节反转）】,d为一个某点莫通道的像素值
    
    if (binary_image.max==0):#全0矩阵判断
        return

    size=np.shape(binary_image)#获取图像大小
    x=size[0]#尺寸获取
    y=size[1]
    #print

    #b=np.where(binary_image[int(size[0]/2)]>0)  #取图像中心点的横坐标x作为扫描行





def skeleton_extraction(binary_image): #骨架提取发获得中轴线、点，使用skimage库，代价是会有毛刺
    from skimage import morphology#用于图形骨架获取
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


#改自幻尔四足巡线代码
def get_x(img,mask):
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
    # 高斯模糊
    gs_frame = cv2.GaussianBlur(img, (5, 5), 0)
    # 转换颜色空间
    hsv = cv2.cvtColor(gs_frame, cv2.COLOR_BGR2HSV)
    # 查找颜色
    mask = cv2.inRange(hsv, color_dist['write']
                       ['Lower'], color_dist['write']['Upper'])
    # 腐蚀
    mask = cv2.erode(mask, None, iterations=2)
    # 膨胀
    mask = cv2.dilate(mask, None, iterations=2)
    # 查找轮廓
    cv2.imshow('mask', mask)
    '''
    
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]
    if len(cnts):
        c = max(cnts, key=cv2.contourArea)  # 找出最大的区域
        area = cv2.contourArea(c)
        # 获取最小外接矩形
        rect = cv2.minAreaRect(c)
        if area >= 500:
            xy = rect[0]
            xy = int(xy[0]), int(xy[1])
            cv2.circle(img, (xy[0], xy[1]), 3, (255, 255, 0), -1)#在中心点坐标绘制圆点
            x = xy[0]
            box = cv2.boxPoints(rect)
            # 数据类型转换
            box = np.int0(box)
            # 绘制轮廓
            cv2.drawContours(img, [box], 0, (0, 255, 255), 1)
    return x
    

