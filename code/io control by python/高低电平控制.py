import numpy as np

img=np.zeros((50,50,3),np.uint8)
ctrl_pin=(38,40)
gpio.setmode(gpio.BOARD)

#gpio.cleanup()


gpio.setup(ctrl_pin, gpio.OUT)
gpio.setwarnings(False)

'''

'''
#if input()=='w':
while True:
    
    cv2.imshow('img',img)
    if cv2.waitKey(1)==ord('w'):
        print('w')
        gpio.output(ctrl_pin, gpio.HIGH)
        
        time.sleep(1)
        gpio.output(ctrl_pin, gpio.LOW)
        
        gpio.cleanup()
    else:
        print('nothing')