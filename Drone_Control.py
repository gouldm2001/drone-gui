import threading
from queue import Empty, Queue
import time

import serial
import msvcrt

import queue

import tkinter as tk
from tkinter import scrolledtext
from tkinter import *
from tkinter.ttk import *


import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import inputs



def millis():
    return round(time.time() * 1000)

quit = False
yaw_list = []
roll_list = []
yaw = 0
roll = 0
pitch = 0

serial_acq_done = False

updateUiQ = Queue(10)
updateUiQ.maxsize=1000
roll_q = Queue(10)

root = Tk()
root.title("Drone Telemetry")

mode = IntVar()

#open the serial port, disable dtr so we don't reset the ardunio everytime
ser = serial.Serial('COM4', dsrdtr=True)
ser.reset_input_buffer()


def write_serial(stringtosend):
    tosend = str(stringtosend) + "\n"
    tosend = tosend.encode()
    print(tosend.decode())
    ser.write(tosend)


fig = plt.figure()
yaw_chart = fig.add_subplot(1,2,1)
roll_chart = fig.add_subplot(1,2,2)

canvas = FigureCanvasTkAgg(fig, master=root) 
canvas.get_tk_widget().grid(row=2, column =0, columnspan=2, rowspan=5)
canvas.draw()

rolllabel = Label(root, text="Roll", )
rolllabel.grid(row=0,column=1)

roll_ind = Entry(root, width = 15)
roll_ind.grid(row=1,column=1)

yawlabel = Label(root, text="Yaw", )
yawlabel.grid(row=0,column=0)

yaw_ind = Entry(root, width = 15)
yaw_ind.grid(row=1,column=0)

modesel_frame = LabelFrame(root,text="Stability Mode" )
modesel_frame.grid(row=2,column=2)

def mode_sel():
    tosend = "mode " + str(mode.get())+ " \n"
    tosend = tosend.encode()
    print(tosend.decode())
    ser.write(tosend)

modesel_init = Radiobutton(modesel_frame, text = 'Init', variable=mode, value = 0, command=mode_sel )
modesel_init.pack(anchor = W)
modesel_pos = Radiobutton(modesel_frame, text = 'Position', variable=mode, value = 1, command=mode_sel )
modesel_pos.pack(anchor = W)
modesel_stab = Radiobutton(modesel_frame, text = 'Rate', variable=mode, value = 2 , command=mode_sel)
modesel_stab.pack(anchor = W)

pidy_frame =  LabelFrame(root,text="Yaw PID" )
pidy_frame.grid(row=3,column=2,columnspan=2)

yawp_ind_label = Label(pidy_frame, text="Prop", )
yawp_ind_label.grid(row = 0, column =0, sticky = W)

yawp_ind = Entry(pidy_frame, width = 15)
yawp_ind.grid(row = 0, column =1, sticky = W)

print(type(yawp_ind))
yawi_ind_label = Label(pidy_frame, text="Int", ).grid(row = 1, column =0, sticky = W)
yawi_ind = Entry(pidy_frame, width = 15)
yawi_ind.grid(row = 1, column = 1, sticky = W)

yawd_ind_label = Label(pidy_frame, text="Deriv", ).grid(row = 2, column =0, sticky = W)
yawd_ind = Entry(pidy_frame, width = 15)
yawd_ind.grid(row = 2, column = 1, sticky = W)

pidr_frame =  LabelFrame(root,text="Roll PID" )
pidr_frame.grid(row=4,column=2,columnspan=2)

rollp_ind_label = Label(pidr_frame, text="Prop", ).grid(row = 0, column =0, sticky = W)
rollp_ind = Entry(pidr_frame, width = 15)
rollp_ind.grid(row = 0, column =1, sticky = W)

rolli_ind_label = Label(pidr_frame, text="Int", ).grid(row = 1, column =0, sticky = W)
rolli_ind = Entry(pidr_frame, width = 15)
rolli_ind.grid(row = 1, column = 1, sticky = W)

rolld_ind_label = Label(pidr_frame, text="Deriv", ).grid(row = 2, column =0, sticky = W)
rolld_ind = Entry(pidr_frame, width = 15)
rolld_ind.grid(row = 2, column = 1, sticky = W)

def getPidParams():
    write_serial("status 1")
    # tosend = "status 1\n"
    # tosend = tosend.encode()
    # print(tosend.decode())
    # ser.write(tosend)

def setPidParams():
 #pid YawPos p 20
    write_serial("pid YawPos p " + str(yawp_ind.get()))
    write_serial("pid YawPos i " + str(yawi_ind.get()))
    write_serial("pid YawPos d " + str(yawd_ind.get()))
    write_serial("pid RollPos p " + str(rollp_ind.get()))
    write_serial("pid RollPos i " + str(rolli_ind.get()))
    write_serial("pid RollPos d " + str(rolld_ind.get()))

getPid = Button(root, text = "Get PID", command = getPidParams)
getPid.grid(row=5,column =2)
setPid = Button(root, text = "Set PID", command = setPidParams)
setPid.grid(row=5,column =3)
 

print(ser.name)
ser.baudrate =115200
ser.timeout = 1
time.sleep(.1)

#clears the command line
buffclr = "\n"
buffclr = buffclr.encode()
ser.write(buffclr) 

def serialAcquisition(serial_port):
    ser.flushInput()
    buffer = ""
    ts  = millis()
    line_cnt =0
    while True:
        
        
        #serial_port.reset_input_buffer()
        data = serial_port.readline()
        line_cnt = line_cnt+1
      

        data_str = data.decode('utf-8', 'backslashreplace')
        
        #check the last line to see if it is complete
        #print(buffer_lines[len(buffer_lines)-1])

        #print(buffer) 

        if data_str != "":
        
            line_input = data_str.split(" ")       

            if line_input[0] == "p:":
                if len(line_input) == 4:
                    yaw = line_input[1]
                    roll = line_input[2]
                    pitch = line_input[3]

                    updateUiQ.put(["yaw",yaw])
                    updateUiQ.put(["roll",roll])

            elif line_input[0] == "s:":
                    
                    mode = line_input[1]
                    updateUiQ.put(["mode",mode])
                    pid_names = ["yawp","yawi","yawd","rollp","rolli","rolld"]
                    i = 2
                    for name in pid_names:
                        updateUiQ.put([name,line_input[i]])
                        i = i + 1
            else:
                print(data_str)
                #parsed_in = 'yaw: '+ yaw + ' roll: ' + roll + " pitch: " + pitch
                #print(parsed_in)


        if quit == True:
            print("serial quitting..")
            break
    updateUiQ.put(["Quit",True])
               
    
sa = threading.Thread(target=serialAcquisition, args = (ser,))
sa.start()

time.sleep(.05)
getPidParams()

write_serial("telem_on 1")

ts2 = millis()
while True:
  
    counter = 0
    #get data from the drone and do things with it
    try:
        while not updateUiQ.empty() :
            command_data = updateUiQ.get()
            counter = counter + 1
            if command_data[0] == "yaw":
                #print("got yaw, "+ command_data[1])              
                yaw_list.append(float(command_data[1]))
            elif command_data[0] == "roll":
                roll_list.append(float(command_data[1]))
            elif command_data[0] == "mode":
                mode.set(int(command_data[1]))
            #pid_names = ["yawp","yawi","yawd","rollp","rolli","rolld"]
            elif command_data[0] == "yawp":
                yawp_ind.delete(0,END)
                yawp_ind.insert(0,command_data[1])    
            elif command_data[0] == "yawi":
                yawi_ind.delete(0,END)
                yawi_ind.insert(0,command_data[1])
            elif command_data[0] == "yawd":
                yawd_ind.delete(0,END)
                yawd_ind.insert(0,command_data[1])
            elif command_data[0] == "rollp":
                rollp_ind.delete(0,END)
                rollp_ind.insert(0,command_data[1])    
            elif command_data[0] == "rolli":
                rolli_ind.delete(0,END)
                rolli_ind.insert(0,command_data[1])
            elif command_data[0] == "rolld":
                rolld_ind.delete(0,END)
                rolld_ind.insert(0,command_data[1])             
        print(counter)
        # if (millis()-ts2) > 1000:
        #     print("got " + str(cnt) + " in one sec")
        #     ts2 = millis()
        #     cnt = 0

        try:
            if (millis()-ts2) > 40:
                if len(yaw_list) > 500:
                    yaw_list=yaw_list[len(yaw_list)-500:len(yaw_list)]
                    roll_list=roll_list[len(roll_list)-500:len(roll_list)]
                
                yaw_ind.delete(0,END)
                yaw_ind.insert(0,yaw_list[len(yaw_list)-1])

                yaw_chart.clear()
                yaw_chart.plot(yaw_list)
                
                roll_ind.delete(0,END)
                roll_ind.insert(0,roll_list[len(roll_list)-1])

                roll_chart.clear()
                roll_chart.plot(roll_list)

                canvas.draw()
                count = 0
                ts2=millis()
                pass
        except:
            pass


        
    except Empty:
        print("EMPTY!!")
       
    
    try:
        root.update()
    except: 
        break
write_serial("telem_on 0")
  
if __name__ == '__main__':
    #root.mainloop()

    
    quit = True
    print("Shutting down serial..")
    
    ts_quit = millis()
    while not serial_acq_done:
        time.sleep(.1)
        command_data = updateUiQ.get()
        
        if command_data[0] == "Quit":
            break
       
        if (millis()-ts_quit)>5000:
            break
    print("Shut down complete")

    ser.close()
    

   
        
        
