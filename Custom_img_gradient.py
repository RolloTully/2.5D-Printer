import cv2, potrace
from numba import jit
from tqdm import tqdm
import numpy as np
from scipy.ndimage import label, generate_binary_structure
import panda3d
kernel = np.ones((3,3),np.uint8)
significance_threshold = 1
def parse(op,img):
    shape = img.shape
    reutrn_array = np.zeros((shape[0]-2,shape[1]-2))
    for x in tqdm(range(1,shape[0]-1,1)):
        for y in range(1,shape[1]-1,1):
            return_array[x-1,y-1] = op(x,y,img)
@parse
def SF(x,y,img):
    region = np.array([img[x-1,y-1],img[x,y-1],img[x+1,y-1],img[x-1,y],img[x+1,y],img[x-1,y+1],img[x,y+1],img[x+1,y+1]])
    region_mean = np.mean(region,axis=0)
    dist = np.sqrt(np.sum(np.square(region_mean-img[x,y])))
    if dist>significance_threshold:
        return 1
    else:
        return 0
@parse
def SF2(x,y,img):
    region = np.array([mask[x-1,y-1],mask[x,y-1],mask[x+1,y-1],mask[x-1,y],mask[x+1,y],mask[x-1,y+1],mask[x,y+1],mask[x+1,y+1]])
    if np.sum(region)>5:
            return 1
        else:
            return 0
@parse
def VGM(x,y,img):
    roi = np.array([img[x-1,y-1]- img[offset_x,offset_y],img[x,y-1]- img[offset_x,offset_y],img[x+1,y-1]- img[offset_x,offset_y],img[x-1,y]- img[offset_x,offset_y],img[x+1,y]- img[offset_x,offset_y],img[x-1,y+1]- img[offset_x,offset_y],img[x,y+1]- img[offset_x,offset_y],img[x+1,y+1]- img[offset_x,offset_y]])
    distance = np.array([1/1.4,1,1/1.4, 1,1, 1/1.4,1,1/1.4])
    normalized = roi*distance
    VGM_Magnitude = np.sum(normalized,axis=0)
    return VGM_magnitude)
def Unsharpen(img):
    gaussian = cv2.GaussianBlur(img,(0,0),2.0)
    return cv2.addWeighted(img,1.5,gaussian,-0.5,0,img)
input_img = cv2.imread("reg2.jpg",0)
#input_img = cv2.resize(input_img,(400,225))
#input_img = cv2.blur(input_img,(3,3))
input_img = Unsharpen(255-input_img)
significance_mask = SF(input_img)
VGM_mask = VGM(input_img)
new_shape = significance_mask.shape
VGM_mask = cv2.resize(VGM_mask, (new_shape[1],new_shape[0]))
ret, VGM_mask = cv2.threshold(VGM_mask,127,255,cv2.THRESH_BINARY)

#print(VGM_mask.shape,significance_mask.shape)
compared = np.logical_and(VGM_mask,significance_mask).astype(np.uint8)
print(np.max(compared))

cv2.imshow("SF",significance_mask)
cv2.imshow("VGM",VGM_mask)
cv2.imshow("and",compared*255)
cv2.waitKey(0)

#
#imput_img = cv2.blur(input_img,(7,7))
#

#output1 = VGM(input_img)
#eroded = cv2.erode(output1,kernel)
#cv2.imshow("output1",output1)
#cv2.imshow("eroded",eroded)
#cv2.waitKey(2000)
