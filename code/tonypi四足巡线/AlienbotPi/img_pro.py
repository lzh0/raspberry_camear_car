# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
import cv2 as cv
import math
from compute_angle import *


def two_distance(start, end):
    """
    计算两点的距离
    :param start: 开始点
    :param end: 结束点
    :return: 返回两点之间的距离
    """
    s_x = start[0]
    s_y = start[1]
    e_x = end[0]
    e_y = end[1]
    x = s_x - e_x
    y = s_y - e_y
    return math.sqrt((x**2)+(y**2))


def get_max_coutour(cou, max_area):
    '''
    找出最大的轮廓
    根据面积来计算，找到最大后，判断是否小于最小面积，如果小于侧放弃
    :param cou: 轮廓
    :return: 返回最大轮廓
    '''
    max_coutours = 0
    r_c = None
    cc = None
    if len(cou) < 1:
        return None
    else:
        for c in cou:
            # 计算面积
            temp_coutours = math.fabs(cv.contourArea(c))
            if temp_coutours > max_coutours:
                max_coutours = temp_coutours
                cc = c
        # 判断所有轮廓中最大的面积
        # print(max_coutours)
        if max_coutours > max_area:
            r_c = cc
        return r_c


def find_contours(binary, max_area):
    '''
    mode  提取模式.
    CV_RETR_EXTERNAL - 只提取最外层的轮廓
    CV_RETR_LIST - 提取所有轮廓，并且放置在 list 中
    CV_RETR_CCOMP - 提取所有轮廓，并且将其组织为两层的 hierarchy: 顶层为连通域的外围边界，次层为洞的内层边界。
    CV_RETR_TREE - 提取所有轮廓，并且重构嵌套轮廓的全部 hierarchy
    method  逼近方法 (对所有节点, 不包括使用内部逼近的 CV_RETR_RUNS).
    CV_CHAIN_CODE - Freeman 链码的输出轮廓. 其它方法输出多边形(定点序列).
    CV_CHAIN_APPROX_NONE - 将所有点由链码形式翻译(转化）为点序列形式
    CV_CHAIN_APPROX_SIMPLE - 压缩水平、垂直和对角分割，即函数只保留末端的象素点;
    CV_CHAIN_APPROX_TC89_L1,
    CV_CHAIN_APPROX_TC89_KCOS - 应用 Teh-Chin 链逼近算法. CV_LINK_RUNS - 通过连接为 1 的水平碎片使用完全不同的轮廓提取算法
    :param binary: 传入的二值图像
    :return: 返回最大轮廓
    '''
    # img, contours, hierarchy = cv.findContours(skin1, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    # 找出所有轮廓
    _, contours, hierarchy = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    # 返回最大轮廓
    return get_max_coutour(contours, max_area)


def image_process(image):
    '''
    # 光线影响，请修改 cb的范围
    # 正常黄种人的Cr分量大约在140~160之间
    识别肤色
    :param image: 图像
    :return: 识别后的二值图像
    '''
    YCC = cv.cvtColor(image, cv.COLOR_BGR2YCR_CB)  # 将图片转化为YCrCb
    Y, Cr, Cb = cv.split(YCC)  # 分割YCrCb
    # Cr = cv2.inRange(Cr, 138, 175)
    Cr = cv.inRange(Cr, 132, 175)
    Cb = cv.inRange(Cb, 100, 140)
    Cb = cv.bitwise_and(Cb, Cr)
    # 开运算，去除噪点
    open_element = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
    opend = cv.morphologyEx(Cb, cv.MORPH_OPEN, open_element)
    # 腐蚀
    kernel = np.ones((3, 3), np.uint8)
    erosion = cv.erode(opend, kernel, iterations=1)
    # cv.imshow('1', erosion)
    return erosion


def get_heart_palms(binary_image):
    """
    获取手掌掌心坐标, 外接圆半径
    :param binary_image: 图像的二值图像
    :return: 掌心坐标，和外接圆半径
    """
    # 提高运算速度方法， 把手掌最小外接矩形的图像传入处理
    # Finding sure foreground area
    # 距离变换的基本含义是计算一个图像中非零像素点到最近的零像素点的距离，也就是到零像素点的最短距离
    # 个最常见的距离变换算法就是通过连续的腐蚀操作来实现，腐蚀操作的停止条件是所有前景像素都被完全
    # 腐蚀。这样根据腐蚀的先后顺序，我们就得到各个前景像素点到前景中心呗Ⅵ像素点的
    # 距离。根据各个像素点的距离值，设置为不同的灰度值。这样就完成了二值图像的距离变换
    # cv2.distanceTransform(src, distanceType, maskSize)
    # 第二个参数 0,1,2 分别表示 CV_DIST_L1, CV_DIST_L2 , CV_DIST_C
    # 获取掌心位置
    dist_transform = cv.distanceTransform(binary_image, 1, 5)
    ret, sure_fg = cv.threshold(dist_transform, 0.8 * dist_transform.max(), 255, 0)
    # ret, sure_fg1 = cv2.threshold(dist_transform, 0.7*dist_transform.max(), 255, 1)
    sure_fg = np.uint8(sure_fg)
    element = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
    sure_fg = cv.morphologyEx(sure_fg, cv.MORPH_OPEN, element)  # 做开运算
    # sure_fg = cv.morphologyEx(sure_fg, cv.MORPH_CLOSE, element)  # 做开运算
    cv.imshow("2", np.hstack([binary_image, sure_fg]))
    cnts = cv.findContours(sure_fg.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)[-2]
    if len(cnts) > 0:
        cy = 0
        for i in cnts:
            ((x, y), radius) = cv.minEnclosingCircle(i)
            if y >= cy:
                cy = int(y)
                cx = int(x)
                maxdis = int(radius)
        return (cx, cy), maxdis
    else:
        return None


def get_defects_far(defects, contours, img):
    '''
    获取凸包中最远的点
    '''
    if defects is None and contours is None:
        return None
    far_list = []
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0]
        start = tuple(contours[s][0])
        end = tuple(contours[e][0])
        far = tuple(contours[f][0])
        # 求两点之间的距离
        a = two_distance(start, end)
        b = two_distance(start, far)
        c = two_distance(end, far)
        # print('a=', a)
        # print('b= ', b)
        # print('c= ', c)
        # 求出手指之间的角度
        angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 180 / math.pi
        # 手指之间的角度一般不会大于100度
        # 小于90度
        if angle <= 75:  # 90:
            # cv.circle(img, far, 10, [0, 0, 255], 1)
            far_list.append(far)
    return far_list


def get_hand_number(binary_image, rgb_image):
    '''
    返回手指的个数
    :param binary_image:
    :param rgb_image:
    :return:
    '''
    # # 2、找出手指尖的位置
    # # 查找轮廓，返回最大轮廓
    contours = find_contours(binary_image, 4000)
    coord_list = []
    if contours is not None:
        # 周长  0.035 根据识别情况修改，识别越好，越小
        epsilon = 0.025 * cv.arcLength(contours, True)
        # 轮廓相似
        approx = cv.approxPolyDP(contours, epsilon, True)
        cv.polylines(rgb_image, [approx], True, (0, 255, 0), 2)
        try:
            if approx.shape[0] >= 3:  # 有三个点以上
                approx_list = []
                for j in range(approx.shape[0]):
                    approx_list.append(approx[j][0])
                approx_list.append(approx[0][0])    # 在末尾添加第一个点
                approx_list.append(approx[1][0])    # 在末尾添加第二个点
                for i in range(1, len(approx_list) - 1):
                    p1 = Point(approx_list[i - 1][0], approx_list[i - 1][1])    # 声明一个点
                    p2 = Point(approx_list[i][0], approx_list[i][1])
                    p3 = Point(approx_list[i + 1][0], approx_list[i + 1][1])
                    line1 = Line(p1, p2)    # 声明一条直线
                    line2 = Line(p2, p3)
                    angle = GetCrossAngle(line1, line2)     # 获取两条直线的夹角
                    angle = 180 - angle     #
                    # print angle
                    if angle < 40:  # 求出两线相交的角度，并小于37度的
                        # cv.circle(rgb_image, tuple(approx_list[i]), 5, [255, 0, 0], -1)
                        coord_list.append(tuple(approx_list[i]))
        except Exception as e:
            print ('shape111', e)
        ##############################################################################
        # 去除手指间的点
        # 1、获取凸包缺陷点，最远点点
        # cv.drawContours(rgb_image, contours, -1, (255, 0, 0), 1)
        hull = cv.convexHull(contours, returnPoints=False)
        # 找凸包缺陷点 。返回的数据， 【起点，终点， 最远的点， 到最远点的近似距离】
        defects = cv.convexityDefects(contours, hull)
        # 返回手指间的点
        hand_coord = get_defects_far(defects, contours, rgb_image)
        # print 'h', hand_coord
        # print 'c', coord_list
        # 2、从coord_list 去除最远点
        new_hand_list = []  # 获取最终的手指间坐标
        alike_flag = False
        if len(coord_list) > 0:
            for l in range(len(coord_list)):
                for k in range(len(hand_coord)):
                    if (-10 <= coord_list[l][0] - hand_coord[k][0] <= 10 and
                            -10 <= coord_list[l][1] - hand_coord[k][1] <= 10):    # 最比较X,Y轴, 相近的去除
                        alike_flag = True
                        break   #
                if alike_flag is False:
                    new_hand_list.append(coord_list[l])
                alike_flag = False

            # print new_hand_list
            # 获取指尖的坐标列表并显示
            for i in new_hand_list:
                cv.circle(rgb_image, tuple(i), 5, [0, 0, 100], -1)

        if new_hand_list is []:
            return 0
        else:
            return len(new_hand_list)
    else:
        return None
