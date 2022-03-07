#import mytest #自制模块编写测试，文件名好像不能有下划线，并且若与启动文件不在同目录需在搜索路径中添加
import FindCentrePoint as fcp
import cv2 
import numpy as np 

#import matplotlib.pyplot as plt
#import scipy.ndimage as ndi
#mytest.tphel()
img=cv2.imread('E:\\road.jpg')
def image_processing(original_image,recognition_mode:str,img_display:bool):
    img=original_image

    fcp.import_successful()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)#彩图转黑白灰度度，后续优化可以针对地图颜色更改RBG转灰度占比#http://www.opencv.org.cn/opencvdoc/2.3.2/html/modules/imgproc/doc/miscellaneous_transformations.html?highlight=cvtcolor#cv2.cvtColor

    gray = cv2.GaussianBlur(gray,(5,5),0,0)#高斯模糊(滤波)，该处理应在灰度前还是后，存疑
    retval, binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)# 大津法二值化，注意输出二值分别为0和255#https://zhuanlan.zhihu.com/p/95034826

    #对于白线深色的地图，去噪点选用先腐蚀再膨胀的方法；黑线白底反之。

    binary_image_pro = cv2.dilate(binary_image, None, iterations=4)#膨胀，白区域变大，最后的参数为迭代次数，腐蚀膨胀顺序与迭代次数视实际情况而定
    binary_image_sub = cv2.erode(binary_image, None, iterations=4)# 腐蚀，白区域变小
    binary_image_process_finish = cv2.dilate(binary_image_sub, None, iterations=4)# 膨胀，白区域变大

    if recognition_mode=='skeleton_extraction':
        #骨架提取模式
        a,b,skeleton=fcp.skeleton_extraction(binary_image_process_finish.copy())
    elif recognition_mode=='get_x':
        x_location=fcp.get_x(img,binary_image_process_finish.copy())
        print(x_location)
        return x_location
    

    if img_display:
        #True
        cv2.imshow('img',img)
        cv2.imshow('gray',gray)
        cv2.imshow('binary_image',binary_image)
        cv2.imshow('binary_image_sub',binary_image_sub)
        cv2.imshow('binary_image_pro',binary_image_pro)
        cv2.imshow('skeleton',skeleton)
        cv2.imshow('binary_image_process_finish',binary_image_process_finish)
        cv2.waitKey(0)
    return print('finish')

#image_processing(img,'get_x',True)

'''
#玩摄像头
cap = cv2.VideoCapture(0)
while True:
    ret, img = cap.read()


    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)#彩图转黑白灰度度#http://www.opencv.org.cn/opencvdoc/2.3.2/html/modules/imgproc/doc/miscellaneous_transformations.html?highlight=cvtcolor#cv2.cvtColor
    retval, binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)# 大津法二值化#https://zhuanlan.zhihu.com/p/95034826
    binary_image_pro = cv2.dilate(binary_image, None, iterations=1)#膨胀，白区域变大，最后的参数为迭代次数
    binary_image_sub = cv2.erode(binary_image, None, iterations=4)# 腐蚀，白区域变小
    cv2.imshow('img',img)
    cv2.imshow('gray',gray)
    cv2.imshow('binary_image',binary_image)
    cv2.imshow('binary_image_sub',binary_image_sub)
    cv2.imshow('binary_image_pro',binary_image_pro)
    cv2.waitKey(1)
'''