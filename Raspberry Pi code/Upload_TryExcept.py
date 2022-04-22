#script for uploading geophone readings to the web server

import os
import glob
import time
import pandas
import requests
from os.path import exists
import serial
import logging
from datetime import datetime

#function to reset the 4G HAT using minicom commands over serial connection
def reset():
    try:
        ser = serial.Serial('/dev/ttyUSB1',115200)                                                                      #try to establish a serial connection to USB1
        print('USB1')
    
    except:
        ser = serial.Serial('/dev/ttyS0',115200)                                                                        #try to establish a serial connection to S0
        print('S0')
    
    command = 'AT\r\n'                                                                                                  #send initial AT command
    ser.write(command.encode())
    
    command = 'AT+CRESET\r\n'                                                                                           #perform the reset using the AT command
    ser.write(command.encode())

    ser.close()                                                                                                         #close the serial connection
    
    time.sleep(30)                                                                                                      #wait 30s to allow the HAT to reconnect


#function to check the running time of the program and reboot the Pi when required (called throughout this script)
def timecheck():
    currenttime = time.time()                                                                                           #record the current time
    uptime = currenttime - starttime                                                                                    #calculate the uptime from the current time and start time
    print(uptime)
    if uptime > 3600 and exist != True:                                                                                 #if device has been on for over 1 hour and is up to date then reboot
        os.system('sudo reboot')
    elif uptime > 5400:                                                                                                 #if device has been on for over 1.5 hours then reboot, even if not up to date
        os.system('sudo reboot')
        

#function to write any errors to an error log file        
def errorlog(e):
    f = open("/home/pi/Sensing/errorlog.txt", "a")                                                                      #open the error log file
    t = datetime.now()                                                                                                  #record the current time
    f.write("\n" + str(e) + " @ " + str(t))                                                                             #write the error message and the time it occured
    f.close()                                                                                                           #close the file
        

#clear any old files from the Logs folder
files = glob.glob('/home/pi/Sensing/Logs/*')
for f in files:
    os.remove(f)

#initialise variables    
failed = 0
counter = 1
check = 0

time.sleep(15)
starttime = time.time()                                                                                                 #record time the program started to send files

while True:
    
    path = '/home/pi/Sensing/Logs/Geophone_out_'+str(counter)+'.csv'                                                    #set up file name path
    
    exist = os.path.exists(path)                                                                                        #check the file exists
    
    timecheck()
    
    while exist != True:                                                                                                #if file doesn't exist wait 10s before checking again
        
        print("no file to send")
        time.sleep(10)
        exist = os.path.exists(path)                                                                                    #re-check if the file exists
        timecheck()
        
    new_data = pandas.read_csv(path).to_dict(orient='list')                                                             #read the data in the file to a dictionary of lists
    
    while True:
        try:
            timecheck()
            check = requests.get('https://em501-landslide-monitoring.azurewebsites.net/check', timeout=60)              #perform get request to check if server is up/an internet connection is available
            timecheck()
    
        except requests.Timeout:                                                                                        #if the request times out, try again
            pass
        
        except requests.exceptions.ConnectionError as e:                                                                #if a connection error occurs, log the error, print it, reset the HAT and increment the fail counter
            errorlog(e)
            print(e)
            print("resetting HAT")
            reset()
            failed = failed + 1
            
            if failed > 10:                                                                                             #if 10 errors occur in a row, reboot the Pi
                os.system('sudo reboot')
    
        except requests.exceptions.RequestException as e:                                                               #if another error occurs, log the error, print it, and increment the fail counter
            timecheck()
            errorlog(e)
            print(e)
            print("Failed to connect")
            time.sleep(10)
            failed = failed + 1
            
            if failed > 10:                                                                                             #if 10 errors occur in a row, reboot the pi
                os.system('sudo reboot')
        
        else:
            if check.text == "yes":                                                                                     #check the get request has obtained the text "yes", which confirms the web server is ready
                print("yes")
                failed = 0                                                                                              #reset the fail counter
                break                                                                                                   #break from the while loop and continue onto the post request for this file
            else:                                                                                                       #if the text is not "yes" then wait 10s and try the request again
                print(check.status_code)
                print("no")
                time.sleep(10)
    
    while True:
        try:
            timecheck()
            start = time.time()
            a = requests.post('https://em501-landslide-monitoring.azurewebsites.net/add', data=new_data, timeout=60)    #perform the post request to send the data
            timecheck()
            end = time.time()
        
        except requests.Timeout:                                                                                        #if the request times out, try again
            pass
        
        except requests.exceptions.ConnectionError as e:                                                                #if a connection error occurs, log the error, print it, reset the HAT and increment the fail counter
            errorlog(e)
            print(e)
            print("resetting HAT")
            reset()
            failed = failed + 1
            
            if failed > 10:                                                                                             #if 10 errors occur in a row, reboot the pi
                os.system('sudo reboot')
        
        except requests.exceptions.RequestException as e:                                                               #if another error occurs, log the error, print it, and increment the fail counter
            timecheck()
            errorlog(e)
            print(e)
            print("Failed to Post")
            time.sleep(10)
            failed = failed + 1
            new_data = pandas.read_csv(path).to_dict(orient='list')                                                     #re-read the data from the file
            
            if failed > 10:                                                                                             #if 10 errors occur in a row, reboot the pi
                os.system('sudo reboot')
        
        else:                                                                                                           #once the file has sent, print the status code for the request, the time taken and the file number
            print(a.status_code)
            print(end - start)
            print(counter)
    
            failed = 0                                                                                                  #reset the fail counter
            x = counter - 2                                                                                             #
            oldfile = '/home/pi/Sensing/Logs/Geophone_out_'+str(x)+'.csv'                                               #set up the path for a previous file
    
            if os.path.isfile(oldfile):                                                                                 #if the file exists, remove it
                os.remove(oldfile)
    
            counter = counter + 1                                                                                       #increment the file name counter
            
            break                                                                                                       #break from the while loop and return to the start for the next file
