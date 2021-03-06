from scipy.ndimage import label, generate_binary_structure
from random import randint,choice, triangular
from scipy.integrate import odeint
import numpy as np
import cv2
from tqdm import tqdm
import matplotlib.pyplot as plt
import serial
from numba import jit

class Serial_COM(object):
    def __init__(self,COM='COM4',BAUD= 115200):
        self.serial_port = serial.Serial(COM,BAUD)
    def Send(self, command):
        self.encoded_command = command.encode()
        self.serial_port.write(self.encoded_command)

class Plotter():
    def __init__(self):
        self.serial_com = Serial_COM()
        self.offset_x = 26
        self.offset_y = 47
        self.offset_z = 7
        self.Home()
        self.Depth_cali(5,3)
    def GoTo(self,x,y,z=10):
        self.serial_com.Send('G0 F7000 X'+str(x+self.offset_x)+' Y '+str(y+self.offset_y)+' Z '+str(z+self.offset_z)+'\r\n')

    def Home(self):
        self.pen_position = False
        self.serial_com.Send('G28 X\r\n G28 Y\r\n G28 Z\r\nG90\r\n G1 F2000 Z5\r\nG1 F2000 X0 Y64\r\n')
    def Depth_cali(self, Start, End):
        self.y = 10
        self.serial_com.Send('G0 Y '+str(self.offset_y)+'X 130 Z 10\r\n')
        for self.depth in range(Start*10, End*10, -1):
            print(self.depth)
            self.serial_com.Send('G0 Y '+str(self.y+self.offset_y)+'X 140 Z'+str(self.depth/10)+'\r\n')
            self.serial_com.Send('G0 Y '+str(self.y+self.offset_y)+'X 160 Z'+str(self.depth/10)+'\r\n')
            self.y += 3
            self.right = input("Is the line sufficent(y/n): ")
            if self.right == "y":
                self.offset_z = self.depth/10
                break
            self.pen_up()
    def Spiral_level(self):
        self.GoTo(150,150,20)
        for self.theta in range(0,10000,1):
            self.theta = (self.theta/100)*np.pi
            self.r = 0.3*self.theta
            self.x = self.r*np.cos(self.theta)
            self.y = self.r*np.sin(self.theta)
            self.GoTo(self.x+100,self.y+100,0)


    def pen_up(self):
        self.serial_com.Send('G0 Z 10\r\n')
    def pen_down(self):
        self.serial_com.Send('G0 Z'+str(self.offset_z)+'\r\n')
    def pen_load(self):
        self.colour = choice(["Red","Green","blue"])

        self.serial_com.Send("G0 F1000 X0 Y0 Z100\r\n")
        input("please insert "+self.colour)
        self.serial_com.Send("G0 F1000 Z10\r\n")
    def infill(self, region):

        self.points = np.where(region != 0)
        self.points = [[self.points[0][self.index],self.points[1][self.index]] for self.index in range(len(self.points[0]))]
        self.serial_com.Send('G1 F7000 X'+str((self.points[0][0]/10)+self.offset_x)+' Y'+str((self.points[0][1]/10) + self.offset_y)+' Z 7'+'\r\nG0 Z'+str(self.offset_z)+'\r\n')# move to the start of the curve

        for index in range(0,len(self.points)-1):
            self.x,self.y=self.points[index]
            self.x_next, self.y_next = self.points[index+1]
            if np.hypot(self.x-self.x_next,self.y-self.y_next) > 2:
                #if the next point isnt imeadiatly adjacent to the currently point then it 'jumps' the gap
                self.serial_com.Send('G0 F7000 X'+str((self.x/10)+self.offset_x)+' Y'+str((self.y/10) + self.offset_y)+' Z '+str(self.offset_z)+'\r\n')
                self.pen_up()
                print("Up ")
                print('G0 F2000 X '+str((self.x_next/10)+self.offset_x)+' Y '+str((self.y_next/10) + self.offset_y)+'\r\n')
                self.serial_com.Send('G0 F7000 X '+str((self.x_next/10)+self.offset_x)+' Y '+str((self.y_next/10) + self.offset_y)+'\r\n')
                self.pen_down()
                print("Down ")
            else:
                pass

        self.command = 'G0 F7000 X'+str((self.points[len(self.points)-1][0]/10)+self.offset_x)+' Y'+str((self.points[len(self.points)-1][1]/10) + self.offset_y)+' Z '+str(self.offset_z)+'\r\n'
        self.serial_com.Send(self.command)
        self.pen_up()

    def Draw_Raw(self, curve):
        self.serial_com.Send('G1 F7000 X'+str((curve[0][0]/10)+self.offset_x)+' Y'+str((curve[0][1]/10) + self.offset_y)+' Z 7'+'\r\n')# move to the start of the curve
        self.pen_down() #places pen to start drawing the curve
        for index in range(0,len(curve)-1):
            self.x,self.y=curve[index]
            self.serial_com.Send('G0 F7000 X '+str(self.x+self.offset_x)+' Y '+str(self.y + self.offset_y)+'\r\n')
        self.command = 'G1 F7000 X'+str((curve[len(curve)-1][0]/10)+self.offset_x)+' Y'+str((curve[len(curve)-1][1]/10) + self.offset_y)+' Z '+str(self.offset_z)+'\r\n'
        self.pen_up()
        self.serial_com.Send(self.command)



    def Draw_curve(self,curve):
        self.serial_com.Send('G1 F7000 X'+str((curve[0][0]/10)+self.offset_x)+' Y'+str((curve[0][1]/10) + self.offset_y)+' Z 7'+'\r\n')# move to the start of the curve
        self.pen_down() #places pen to start drawing the curve
        for index in range(0,len(curve)-1):
            self.x,self.y=curve[index]
            print("Moving to: ",self.x," ",self.y)
            self.x_next, self.y_next = curve[index+1]
            if np.hypot(self.x-self.x_next,self.y-self.y_next) > 2:
                #if the next point isnt imeadiatly adjacent to the currently point then it 'jumps' the gap
                self.pen_up()
                self.serial_com.Send('G0 F2000 X '+str((self.x_next/10)+self.offset_x)+' Y '+str((self.y_next/10) + self.offset_y)+'\r\n')
                self.pen_down()
            else:
                self.serial_com.Send('G0 F7000 X'+str((self.x/10)+self.offset_x)+' Y'+str((self.y/10) + self.offset_y)+' Z '+str(self.offset_z)+'\r\n')
        self.command = 'G1 F7000 X'+str((curve[len(curve)-1][0]/10)+self.offset_x)+' Y'+str((curve[len(curve)-1][1]/10) + self.offset_y)+' Z '+str(self.offset_z)+'\r\n'
        self.serial_com.Send(self.command)
        self.pen_up()

class Curve(object):
    def __init__(self, point_array, curve_start = None):
        self.curve_start = curve_start
        self.points = point_array
        self.centre = np.mean(self.points,axis=0)
        self.mask = []
        print("curve created, this curve is composed of "+str(len(self.points))+" points.")
        self.order_points() # orders all points



    def order_points(self): # perfomrms curve reconstructipn so allow drawing
        ''' Fairly proud of this, just fairly simple curve reconstruction'''
        self.original_points = self.points.copy()
        self.index_order = []
        if self.curve_start==None:
            self.distances = [np.sum(np.array([np.hypot(self.S_point[0]-self.E_point[0],self.S_point[1]-self.E_point[1])for self.E_point in self.points])) for self.S_point in tqdm(self.points)]
            self.working_index  = np.argmax(self.distances)
        else:
            self.distances = [np.hypot(self.S_point[0]-self.curve_start[0],self.S_point[1]-self.curve_start[1]) for self.S_point in tqdm(self.points)]
            self.working_index  = np.argmax(self.distances)

        for x in tqdm(range(len(self.points))):
            self.index_order.append(self.working_index)
            self.distances = np.array([np.hypot(self.points[self.working_index][0]-self.point[0],self.points[self.working_index][1]-self.point[1])for self.point in self.points])
            self.distances[self.distances==0]=1000000000000
            self.new_working_index=np.argmin(self.distances)
            self.points[self.working_index]=[100000000000,10000000000]
            self.working_index = self.new_working_index
        self.ordered_coordinates = []
        for self.index in self.index_order:
            self.ordered_coordinates.append(self.original_points[self.index])
        self.points=self.ordered_coordinates
    def __getitem__(self,k):
        return self.points[k]
    def __len__(self):
        return len(self.points)

class Region(object):
    def __init__(self, region):
        self.region_mask = region

    def Compute_Path(self):
        self.layers = []
        self.region_curves = []
        '''Uses Edge detection to compute an efficent path'''
        self.region_mask[self.region_mask != (0 or 0.0)]=255
        self.region_mask[self.region_mask == (0 or 0.0)]=255
        while np.any(np.where(self.region_mask ==222)):
            self.outer_layer = cv2.Canny(self.region_mask)
            self.region_mask = self.region_mask-self.outer_layer
            self.layer_points = np.where(self.outer_layer>0)
            self.paired_layer_points=[[self.layer_points[0][self.index],self.layer_points[1][self.index]] for self.index in range(len(self.layer_points[0]))]
            self.layers.append(self.paired_layer_points)
        self.first_curve = Curve(self.layer[0])
        self.next_curve_start = self.first_curve.points[len(self.first_curve.points)]
        self.region_curves.append(self.first_curve)
        for self.index in range(1,len(self.layers)-1):
            self.new_curve = Curve(self.layer[index],self.next_curve_start)
            self.next_curve_start = self.new_curve.points[len(self.new_curve.points)]
            self.region_curves.append(self.new_curve)
class Point(object):
    def __init__(self, x, y):
        self.x, self.y = x, y
class Gui():
    def __init__(self):
        pass
class Main():
    def __init__(self):
        #self.plotter = Plotter()
        self.curves = []
        self.x_max=1000
        self.y_max=1000

        self.rho = 28.0
        self.sigma = 10.0
        self.beta = 8.0 / 3.0
        self.output = np.zeros((1360,1360))
        self.mask = np.zeros((1360,1360))
        self.circle_drawing_img = cv2.imread("Circle Drawing Test.jpg")
        self.Circle_Drawing(self.circle_drawing_img)
        #self.plotter.Spiral_level()
        #self.Lorenz_Plot()

        #self.init_frame_img("Test Image.jpg")
        #self.init_frame_circles()
        #self.Circle_Drawing()

    def displacment(self, img, source, sink):
        return -img[source[0], source[1]]/(np.hypot(source-sink))**2
    def Circle_Drawing(self, img):
        self.gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.centers = [Point(randint(0,self.gray.shape[0]-1),randint(0,self.gray.shape[1]-1)) for x in tqdm(range(2000))]
        self.point_display = self.gray.copy()
        for self.point in self.centers:
            self.point_display[self.point.x,self.point.y] =255

        cv2.imshow("Grey", self.gray)
        cv2.imshow("Point origins", self.point_display)
        cv2.waitKey(0)


    def Lorenz_operator(self, state, t):
        self.x, self.y, self.z = state  # Unpack the state vector
        return self.sigma * (self.y - self.x), self.x * (self.rho - self.z) - self.y, self.x * self.y - self.beta * self.z
    def Lorenz_Plot(self):
        self.intervals = np.arange(0.0, 80.0, 0.005)
        self.states = odeint(self.Lorenz_operator, [3.0, 3.0, 3.0], self.intervals)
        self.coords = [self.states[:,0],self.states[:,1]]
        print(np.min(self.coords), np.max(self.coords))
        self.coords = self.coords+ abs(np.min(self.coords))
        print(np.min(self.coords), np.max(self.coords))
        self.coords = self.coords*(180/np.max(self.coords))
        self.coords = np.round(self.coords,3)
        print(np.min(self.coords), np.max(self.coords))
        print(self.coords)
        self.paired_points=[[self.coords[0][self.index],self.coords[1][self.index]] for self.index in range(len(self.coords[0]))]
        self.plotter.Draw_Raw(self.paired_points)



        return

    def init_frame_circles(self):
        self.output = np.zeros((1360,1360))
        self.first_circle = [randint(0,self.x_max),randint(0,self.y_max),100]
        cv2.circle(self.output,(680,680),500,255,1)
        self.mask = np.zeros((1360,1360))
        cv2.circle(self.mask,(680,680),500,255,-1)

    def init_frame_img(self,path):
        self.img = cv2.imread(path,0)
        self.working_img = self.img.copy()
        self.mask = 255-self.working_img
        self.output = cv2.Canny(self.mask,100,200)

    def Arc_Drawing(self):
        print("Computing path... Please wait.")
        #self.points = np.where(self.output!=0)
        #self.line_points=[[self.points[0][self.index],self.points[1][self.index]] for self.index in range(len(self.points[0]))]
        #self.curves.append(Curve(self.line_points))

        for cir in tqdm(range(3)):
            '''forces all sources to lie on the boundary of a  previous circle thus reducing cramming'''
            #self.source_points = np.where(self.output > 0)
            #self.new_points = [[self.source_points[0][self.index],self.source_points[1][self.index]] for self.index in range(len(self.source_points[0]))]
            #self.new_source = choice(self.new_points)
            self.new_source = [randint(0,1360),randint(0,1360)] #randomly choices the centre of the next circle
            self.circle = np.zeros((1360,1360))
            self.radius = int(triangular(50,200,80)) # randomly-ish sets the new circle radius
            cv2.circle(self.circle,(self.new_source[1],self.new_source[0]),self.radius,255,1) # adds the newly defined circle to the blank mask
            self.difference = self.circle-self.mask # removes all overlapiing portions of the arc
            self.difference[self.difference<127]=0 # just trydying up the data tyes do to a weird quirk of the circle generating function
            self.points = np.where(self.difference!=0) #finds all remaining points of thencircle
            self.line_points=[[self.points[0][self.index],self.points[1][self.index]] for self.index in range(len(self.points[0]))] # pairs up the x,y coordinates of the points
            if self.line_points != []: # weirdly some curves have an arc length of 0
                self.curves.append(Curve(self.line_points)) #defines a curve object
            ''' All the hard work done now is just to allow for a nice preview '''
            self.output = self.output+self.difference
            cv2.circle(self.mask,(self.new_source[1],self.new_source[0]),self.radius,255,-1)
            self.output[self.output!=0.0]=255
            cv2.imshow("output",self.output)
            cv2.waitKey(1)
        cv2.imshow("output",255-self.output)
        cv2.waitKey(0)
        self.lables, self.Rnum = label(255-self.output)
        self.areas = [np.count_nonzero(self.lables == self.i) for self.i in range(self.Rnum)]
        self.max_area_index = np.argmax(self.areas)
        print(self.areas)




        #self.plotter.pen_up()

        for self.curve in tqdm(self.curves):
            if self.curve != []:
                self.plotter.Draw_curve(self.curve)

        self.plotter.serial_com.Send("G1 Z7\r\nG1 X0 Y64\r\nG1 Z4\r\nG1 X136 Y64\r\nG1 X136 Y200\r\nG1 X0 Y200\r\n G1 X0 Y64\r\nG1 Z1000 Z7\r\n")
        self.region_masks = []
        for self.i in range(0,self.Rnum-1):
            if self.i!=self.max_area_index:
                self.region_mask = cv2.inRange(self.lables,self.i,self.i)

                cv2.imshow(" ",cv2.resize(self.region_mask,(900,900)))
                cv2.waitKey(1000)
                self.plotter.pen_load()
                self.plotter.infill(self.region_mask)

if __name__ == "__main__":
    Main()
