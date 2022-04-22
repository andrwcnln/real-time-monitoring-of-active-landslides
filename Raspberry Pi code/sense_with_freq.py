#!/usr/bin/python
# -*- coding:utf-8 -*-


import time
from High_Pricision_AD_HAT.python import utils
import RPi.GPIO as GPIO
import csv
from datetime import datetime 


REF = 5.15 # Modified reference value for pi 5V voltage
                    

def log_sensor_values(log_number): # Function that builds data logs with 5000 (x,y and z) readings
    ADC_Value_Log = [['time','geophone x','geophone y','geophone z']] # initialise first line of log list
    
    t_samp_0 = time.perf_counter() # recording the time before smapling begins
    
    while len(ADC_Value_Log) <= 5000: # length of each data log
        [ADC_Time, ADC_Value] = ADC.ADS1263_GetThree() # gets current ADC values, function made and stored in seperate script
        
        ADC_Values = [datetime.fromtimestamp(ADC_Time)] # logs time when "y" measurement was taken
            
        for i in range(0, 3, 1): # converting x, y and z measurement to decimal value
            if(ADC_Value[i]>>31 ==1):
                ADC_Values.append((REF*2 - ADC_Value[i] * REF / 0x80000000)/80)
            else:
                ADC_Values.append((ADC_Value[i] * REF / 0x7fffffff)/80)# 32bit
                
        ADC_Value_Log.append(ADC_Values) # add converted values to as new reading in log list
                
        time.sleep(0.0025) # sleep in order to provide space between each set of readings
                
    t_samp_1 = time.perf_counter() # record time when stopped sampling (+ wait)
    freq = 5000/(t_samp_1-t_samp_0) # 5000 readings recorded in dt seconds measns frequency of (about 200 Hz)
        
    with open(str('./Logs/Geophone_out_'+str(log_number)+'.csv'),'w') as out_file: # writing log list to log csv file
        write = csv.writer(out_file)
        write.writerows(ADC_Value_Log)
        
    return freq # output the frequency
    
try:
    ADC = utils.ADS1263.ADS1263() # initialise ADC
    if (ADC.ADS1263_init_ADC1('ADS1263_7200SPS') == -1):
        exit()
    ADC.ADS1263_SetMode(0) # initialise ADC
    log = 0 # initialising log counter value, counter will increase with every log made since last pi boot
    f_old = 0 # initialising frequency recorder value, recorder will update with every log made
    
    while True: # run continiously
        log = log + 1 # increase log count
        f_new = log_sensor_values(log) # run log funciton to produce set of 5000 data readings
        f_t = f_old+f_new # calculating updating average frequency
        f_ave = (f_t)/log
        f_old = f_t
        print("rolling average sampling frequency: ",f"{f_ave:.1f} Hz", end="\r") # printing rolling average frequency to command line (in one line - does not work with forked processes)
        
    ADC.ADS1263_Exit() # turn off ADC
    exit()
  
except IOError as e: # print ADC error
    print(e)
    
except KeyboardInterrupt: # allow process to manually interrupted/ stopped
    print("ctrl + c:")
    print("Program end")
    ADC.ADS1263_Exit()
    exit()
   
