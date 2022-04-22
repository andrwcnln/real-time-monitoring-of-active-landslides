#script to run on startup which ensures the raspberry pi has an internet connection

import requests
import time
import os

failed = 0                                              #initialise the fail counter

while True:
    
    try:
        ping = requests.get('https://www.google.com')   #try to ping google using a get request
        
    except:
        time.sleep(10)
        failed = failed + 1                             #if an error occurs, increment the fail counter
        
        if failed > 10:                                 #if it fails more than 10 times then reboot the pi
            os.system('sudo reboot')
    
    else:
        a = ping.status_code                            #if successful then check the status code of the get request
        print(a)
        if a == 200:                                    #if the status code is 200 then break from the while loop, otherwise try again
            break
        
        
time.sleep(60)                                          #wait 60 seconds to ensure the time has updated on the pi
