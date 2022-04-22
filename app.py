# importing dependencies
import sys # for appedning pymongo to path
import os # ^^
from time import time # for basic time operations
import pandas # for manitpulating dicts and arrays

# appending pymongo install location to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '/home/site/wwwroot/pymodules')))

# other dependencies
from flask import Flask, render_template, request, send_file # for Flask back-end of web app
import pymongo # for interacting with database
from pymongo import MongoClient # ^^ 

from datetime import datetime, timedelta # for more complex time calculations

import csv # for reading and writing to CSV files

import matplotlib as mpl # for generating plots
import matplotlib.pyplot as plt # ^^
import numpy as np # for fourier transform

from apscheduler.schedulers.background import BackgroundScheduler # for scheduling plot updates

app = Flask(__name__) # create the Flask app

# setting up database
uri = 'database.connection.string' # this should be replaced with the connection string of your MongoDB 
client = pymongo.MongoClient(uri)

# assigning variables to database and collections
db = client.data # use database 'data'
readings = db.readings # in 'data', collection 'readings'
last_download = db.last_download # collection 'last_download'

# this is the function for generating the plots
def load():
    buffer = [] # reset buffer

    for x in readings.find().sort('_id',pymongo.DESCENDING).limit(5): # load 5 most recent documents from database
        buffer.append(x) # append these to the buffer

    buffer.reverse() # reverse the buffer to so that plot is the right way round

    # initialise variables
    sensor_x = []
    sensor_y = []
    sensor_z = []
    sensor_times = []

    # for each document in the buffer, extract the values and append them to the initialised variable
    for n in range(0,len(buffer)):
        sensor_x = sensor_x + buffer[n]['geophone x']
        sensor_y = sensor_y + buffer[n]['geophone y'] 
        sensor_z = sensor_z + buffer[n]['geophone z']
        sensor_times = sensor_times + buffer[n]['time']

    fig = plt.figure(figsize=(8,6)) # initialise figure
    # create three subplots
    axx = plt.subplot(311)
    axy = plt.subplot(312)
    axz = plt.subplot(313)

    # removing labels from top plot and middle plot x axes
    axx.tick_params(labelbottom=False)
    axy.tick_params(labelbottom=False)

    # setting y axis ticks
    axx.set_yticks([0,5/80])
    axy.set_yticks([0,5/80])
    axz.set_yticks([0,5/80])

    # plotting x, y and z on their respective axes
    axx.plot(sensor_times,sensor_x,color='blue')
    axy.plot(sensor_times,sensor_y,color='red')
    axz.plot(sensor_times,sensor_z,color='green')

    # set limits of y axes to min and max geophone values and x limits to first time and last time
    axx.set_ylim([0,5/80])
    axx.set_xlim([sensor_times[0],sensor_times[-1]])
    axy.set_ylim([0,5/80])
    axy.set_xlim([sensor_times[0],sensor_times[-1]])    
    axz.set_ylim([0,5/80])
    axz.set_xlim([sensor_times[0],sensor_times[-1]])

    # rotate time labels for readability
    for label in axz.get_xticklabels():
        label.set_rotation(20)
        label.set_horizontalalignment('right')

    # set axes labels and title
    axy.set_ylabel('Velocity (m/s)')
    axz.set_xlabel('Time')
    axx.set_title('Velocity of geophones (x, y and z) against time')

    # set legends
    axx.legend('x')
    axy.legend('y')
    axz.legend('z')

    # save the figure as a png and close all open matplotlib windows
    plt.savefig('static/images/plot.png')
    plt.close('all')

    # initialise new plot and subplots
    fig2 = plt.figure(figsize=(8,6))
    axx_ft = plt.subplot(311)
    axy_ft = plt.subplot(312)
    axz_ft = plt.subplot(313)

    # generate fast fourier transform and corresponding frequencies
    ftx = np.fft.fft(sensor_x)
    freqx = np.fft.fftfreq(len(ftx))
    fty = np.fft.fft(sensor_y)
    freqy = np.fft.fftfreq(len(fty))
    ftz = np.fft.fft(sensor_z)
    freqz = np.fft.fftfreq(len(ftz))

    # get timestep to properly scale the frequency axis
    deltat = datetime.timestamp(sensor_times[1]) - datetime.timestamp(sensor_times[0])

    # plot fourier transform and scaled frequencies
    axx_ft.plot((2*freqx)/deltat,abs(ftx),color='blue')
    axy_ft.plot((2*freqy)/deltat,abs(fty),color='red')
    axz_ft.plot((2*freqz)/deltat,abs(ftz),color='green')

    # set x limit to be minimum 0, maximum auto
    axx_ft.set_xlim(left=0)
    axy_ft.set_xlim(left=0)
    axz_ft.set_xlim(left=0)

    # find max value of fft in positive range
    ftx_max = max(abs(ftx[(-len(ftx/2))+1:]))
    fty_max = max(abs(fty[(-len(ftx/2))+1:]))
    ftz_max = max(abs(ftz[(-len(ftx/2))+1:]))

    # scale y axis to maximum value
    axx_ft.set_ylim(top=ftx_max,bottom=0)
    axy_ft.set_ylim(top=fty_max,bottom=0)
    axz_ft.set_ylim(top=ftz_max,bottom=0)

    # set axes labels and title
    axy_ft.set_ylabel('Magnitude')
    axz_ft.set_xlabel('Frequency (Hz)')
    axx_ft.set_title('Corresponding Fourier transforms')

    # set legends
    axx_ft.legend('x')
    axy_ft.legend('y')
    axz_ft.legend('z')

    # save the figure as a png and close all open matplotlib windows
    plt.savefig('static/images/fourier.png')
    plt.close('all')

scheduler = BackgroundScheduler() # initialise a new background scheduler
load_new_data = scheduler.add_job(load, 'interval', seconds=5) # add a job t the scheduler which calls the above function every five seconds
scheduler.start() # start the scheduler

# this is the homepage of the site
@app.route('/')
def landing():
    download_time = last_download.find_one({},{'_id':0}) # find the last download time in the database
    # render the html template landing.html, passing the last download time as a formatted string
    return render_template('landing.html',date = str(download_time['time'].strftime('%A, %B %e %Y at %H:%M:%S')))  

# this is the page where data can be viewed. it is only accesible via a POST request
@app.route('/view', methods = ['POST'])
def view():
    end_date = datetime.now() # set end date to current time
    data_requested = request.form # get data from POST request
    if data_requested['time_range'] == "New data since last downloaded": # if the user selected 'New data since last downloaded'
        download_time = last_download.find_one({},{'_id':0}) # pull the last download time from the database
        start_date = download_time['time'] # set start date as this time
    elif data_requested['time_range'] == "Last minute": # if the user selected 'Last minute'
        start_date = end_date - timedelta(minutes=1) # set the start date 1 minute behind the end date
    elif data_requested['time_range'] == "Last 5 minutes": # if the user selected 'Last 10 minutes'
        start_date = end_date - timedelta(minutes=5) # set the start date 5 minutes behind the end date
    elif data_requested['time_range'] == "Last 10 minutes": # if the user selected 'Last 30 minutes'
        start_date = end_date - timedelta(minutes=10) # set the start date 10 minutes behind the end date
    elif data_requested['time_range'] == "Specify dates and times": # if the user chose to specify their own times'
        start_date = datetime.strptime(data_requested['from'],'%Y-%m-%dT%H:%M') # take the start date specified by the user and parse it into a datetime object
        end_date = datetime.strptime(data_requested['to'],'%Y-%m-%dT%H:%M') # take the end date specified by the user and parse it into a datetime object
    else:
        start_date = 0 # otherwise, the option selected was for all data, so set the start date to 0

    sensor_dict = {'_id':0} # initialise the dictionary for selected data to remove the databse id

    # if all sensors have been selected the add them all to the sensor dict
    if 'all' in data_requested:
        sensor_dict['geophone x'] = 1
        sensor_dict['geophone y'] = 1
        sensor_dict['geophone z'] = 1

    # else, add only the sensors that have been selected in the form
    else:
        if 'geophone x' in data_requested:
            sensor_dict['geophone x'] = 1 
    
        if 'geophone y' in data_requested:
            sensor_dict['geophone y'] = 1 

        if 'geophone z' in data_requested:
            sensor_dict['geophone z'] = 1 

    # if timestamps have been selected then add them as well
    if 'time_stamps' in data_requested:
        sensor_dict['time'] = 1

    sensor_readings = [] # initialise sensor readings variable
    for x in readings.find({'start_time':{'$gte':start_date},'end_time':{'$lte':end_date}},sensor_dict): # finds all readings in time range
        b = pandas.DataFrame(x).to_dict('records') # parse them into individual records
        sensor_readings = sensor_readings + b # append to sensor readings

    title = str(start_date.strftime('%Y/%m/%d %H:%M')) + " - " + str(end_date.strftime('%Y/%m/%d %H:%M')) # make a string of time ranges to be used as the page title
    return render_template('view.html',data = sensor_readings,sensor_dict = sensor_dict,page_title = title) # render view.html, passing the data, the dictionary of required data and the title string

# this is the page where the deivce can add to the database. it is only accesible via a POST request
@app.route('/add', methods = ['POST'])
def add():
    new_data = request.form.to_dict(flat=False) # take data from post request

    # take values from data and make them into variables in Python
    t = new_data['time']
    start_time = datetime.strptime(t[0],'%Y-%m-%d %H:%M:%S.%f') # start time is first time in times list
    end_time = datetime.strptime(t[-1],'%Y-%m-%d %H:%M:%S.%f') # end time is last time in times list
    gX = new_data['geophone x']
    gY = new_data['geophone y']
    gZ = new_data['geophone z']
    
    # convert data to correct format while adding into dict 
    sensor_readings = {
        'time':[datetime.strptime(x,'%Y-%m-%d %H:%M:%S.%f') for x in t], # 2022-03-21 12:25:47.297650
        'geophone x':[float(x) for x in gX],
        'geophone y':[float(x) for x in gY],
        'geophone z':[float(x) for x in gZ],
        'start_time':start_time,
        'end_time':end_time
    }
    
    readings.insert_one(sensor_readings) # insert into database
    print('New data added!') # print to log stream
    return "200" # return success message to the device
    
@app.route('/download', methods = ['POST'])
def download():
    end_date = datetime.now() # set end date to current time
    data_requested = request.form # get data from POST request
    if data_requested['time_range'] == "New data since last downloaded": # if the user selected 'New data since last downloaded'
        download_time = last_download.find_one({},{'_id':0}) # pull the last download time from the database
        start_date = download_time['time'] # set start date as this time
    elif data_requested['time_range'] == "Last minute": # if the user selected 'Last minute'
        start_date = end_date - timedelta(minutes=1) # set the start date 1 minute behind the end date
    elif data_requested['time_range'] == "Last 5 minutes": # if the user selected 'Last 10 minutes'
        start_date = end_date - timedelta(minutes=5) # set the start date 5 minutes behind the end date
    elif data_requested['time_range'] == "Last 10 minutes": # if the user selected 'Last 30 minutes'
        start_date = end_date - timedelta(minutes=10) # set the start date 10 minutes behind the end date
    elif data_requested['time_range'] == "Specify dates and times": # if the user chose to specify their own times'
        start_date = datetime.strptime(data_requested['from'],'%Y-%m-%dT%H:%M') # take the start date specified by the user and parse it into a datetime object
        end_date = datetime.strptime(data_requested['to'],'%Y-%m-%dT%H:%M') # take the end date specified by the user and parse it into a datetime object
    else:
        start_date = 0 # otherwise, the option selected was for all data, so set the start date to 0

    sensor_dict = {'_id':0} # initialise the dictionary for selected data to remove the databse id

    # if all sensors have been selected the add them all to the sensor dict
    if 'all' in data_requested:
        sensor_dict['geophone x'] = 1
        sensor_dict['geophone y'] = 1
        sensor_dict['geophone z'] = 1

    # else, add only the sensors that have been selected in the form
    else:
        if 'geophone x' in data_requested:
            sensor_dict['geophone x'] = 1 
    
        if 'geophone y' in data_requested:
            sensor_dict['geophone y'] = 1 

        if 'geophone z' in data_requested:
            sensor_dict['geophone z'] = 1 

    # if timestamps have been selected then add them as well
    if 'time_stamps' in data_requested:
        sensor_dict['time'] = 1

    sensor_readings = [] # initialise sensor readings variable
    for x in readings.find({'start_time':{'$gte':start_date},'end_time':{'$lte':end_date}},sensor_dict): # finds all readings in time range
        b = pandas.DataFrame(x).to_dict('records') # parse them into individual records
        sensor_readings = sensor_readings + b # append to sensor readings

    last_download.update_one({}, { "$set": { 'time': end_date } }) # update last downloaded time in database
    
    headers = [] # initialise headers variable

    # get headers from the keys in sensor dict
    for key in sensor_dict:
        headers.append(key)
    
    # remove _id from headers
    headers.pop(0)
    
    # open data.csv and wrtie the data to deac row
    with open('data.csv','w',newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for value in sensor_readings:
            writer.writerow(value) 

    return send_file('data.csv', as_attachment=True) # send the file to be downloaded to the user's computer

# this is where the live plots can be viewed. the python simply returns the html file, which updates itself using javascript
@app.route('/plot')
def plot():
    return render_template('plot.html')

# this is where the device can check if the site is up and readty to serve requests
@app.route('/check')
def check():
    return "yes"

# this runs the app
if __name__ == '__main__':
    app.run()

