
'''#废弃代码，历史遗留代码
#get_keyboard_press()用于linux平台下命令行中按键检测
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
        
        if c == '\x1b':         # x1b is ESC    #检测按键按下ESC
            gpio.cleanup()#释放引脚
            cv2.destroyAllWindows()#关闭窗口
            return sys.exit()#结束程序
        
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return str(c)
#搭配代码：
#自己写的get_keyboard_press(),不如用opencv cv2.waitKey(1)....，而且非阻塞还严重漏检按键
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
