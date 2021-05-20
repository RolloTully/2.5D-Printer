import numpy as np
import cv2
blank = np.zeros((1360,1360))
for x in range(0,1350,10):
    for y in range(0,1350,20):
        blank[x,y:y+10]=255
        blank[x+10,y:y+10]=255
cv2.imshow(" ",blank)
cv2.waitKey(0)
