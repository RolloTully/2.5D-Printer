import serial,time,cv2
from tqdm import tqdm
import numpy as np
from scipy.interpolate import splprep, splev
img = cv2.imread('reg.jpg')
img = cv2.resize(img,(190,190))
B = img[:,:,0]
G = img[:,:,1]
R = img[:,:,2]

class Serial_COM(object):
    def __init__(self,COM='COM4',BAUD= 115200):
        self.serial_port = serial.Serial(COM,BAUD)
    def Send(self, command):
        self.encoded_command = command.encode()
        self.serial_port.write(self.encoded_command)

class Image_Processes(object):
    def __init__(self):
        self.kernel = np.ones((3,3),np.uint8)

    def Process_Image(self,img):
        self.gray = (img[:,:,0]+img[:,:,1]+img[:,:,2])/3
        self.canny_edges = cv2.canny(self.gray,30,200)
        cv2.imshow('edge',self.canny_edges)
        cv2.waitKey(0)

    def LoadIm(self,add,q=False):
        self.image = cv2.imread(add)
        if q:
            pass
        else:
            self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            self.denoised = cv2.fastNlMeansDenoising(self.gray,None,10,7,21)
        return self.denoised



    def Compute_Contours(self,img):
        self.blurred = cv2.blur(img,(3,3))
        self.thresh= cv2.adaptiveThreshold(self.blurred,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,2)
        self.cnt,_ = cv2.findContours(self.thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.filtered_cnts = []
        for cnt in self.cnt:
            if len(cnt>10):
                self.filtered_cnts.append(cnt)
        self.cnt = self.filtered_cnts
        self.cnt = sorted(self.cnt,reverse=True,key=len)

        self.contoured_image = cv2.drawContours(np.zeros((380,380)),self.cnt,-1,255,1)
        return self.cnt, self.contoured_image

class Main():
    def __init__(self):
        self.img_add = "ABC.jpg"
        self.image_processes = Image_Processes()
        self.kernel = np.ones((5,5),np.uint8)
        self.serial_com = Serial_COM()
        self.offset_x = 103
        self.offset_y = 170
        self.pen_position = False
        self.MainLoop()

    def G_Code_Parser(self,path):
        self.command_list = []
        for v_pos,state in path:
            print(v_pos)
            self.x_pos = v_pos[0]
            self.y_pos = v_pos[1]
            if state == 0:
                self.z_pos=20
            if state == 1:
                self.z_pos=18.5
            self.command = 'G1 F7000 X'+str(self.offset_x-(self.x_pos))+' Y'+str(self.offset_y-(self.y_pos))+' Z'+str(self.z_pos)+'\r\n'
            self.command_list.append(self.command)
        return self.command_list
    def Compute_Path(self,cnts):
        self.path = []
        for self.cnt in cnts:
            self.path.append([self.cnt[0],0])
            self.path.append([self.cnt[0],1])
            for self.index in  range(1,len(self.cnt)-1):
                self.path.append([self.cnt[self.index],1])
            self.path.append([self.cnt[len(self.cnt)-1],1])
            self.path.append([self.cnt[len(self.cnt)-1],0])
        return self.path
    def Home(self):
        self.pen_position = False
        self.serial_com.Send('G28 X\r\n G28 Y\r\n G28 Z\r\nG90\r\n G1 F2000 Z40\r\nG1 F2000 X5 Y73\r\nG1 F2000 Z18\r\nG1 F2000 Z22\r\n')

    def pen_up(self):
        self.pen_positon = False
        self.serial_com.Send('G1 Z22\r\n')

    def pen_down(self):
        self.pen_position = True
        self.serial_com.Send('G1 Z18.5\r\n')

    def Border(self):
        self.pen_down()
        self.serial_com.Send('G1 X5 Y73\r\nG1 X190 Y73\r\nG1 X190 Y200\r\nG1 X5 Y200\r\n G1 X5 Y73\r\n')
    def Custom(self,array):
        for command in tqdm(array):
            print(command)
            self.serial_com.Send(command)
    def Recast_Contours(self,array,a=1,b=1):
        self.recasted = []
        for cnt in array:
            self.recasted_contour = []
            for point in cnt:
                self.recasted_contour.append([round(point[0,0]/a,2) ,round(point[0,1]/b,2)])
            self.recasted.append(self.recasted_contour)
        return self.recasted


    def MainLoop(self):
        #self.Home()
        self.denoised = self.image_processes.LoadIm(self.img_add)
        self.denoised = cv2.dilate(self.denoised,self.kernel,5)
        self.cnts,_ = self.image_processes.Compute_Contours(self.denoised)
        print(self.denoised.shape)
        print( max(self.denoised.shape),np.argmax(self.denoised.shape))
        self.Scale_Factor = max(self.denoised.shape)/[130,190][np.argmax(self.denoised.shape)]
        print(np.array(self.denoised.shape)/self.Scale_Factor,self.Scale_Factor)

        self.recasted = self.Recast_Contours(self.cnts,self.Scale_Factor,self.Scale_Factor)
        cv2.imshow('preview',_)
        cv2.waitKey(0)
        cv2.imwrite("Current_img.jpg",_)
        self.path = self.Compute_Path(self.recasted)
        self.command_list = self.G_Code_Parser(self.path)
        #self.Custom(self.command_list)

        if serial_port.is_open:
            serial_port.close()
if __name__ =='__main__':
    Main( )
