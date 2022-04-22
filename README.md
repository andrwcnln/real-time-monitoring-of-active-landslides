# Real-time Monitoring of Active Landslides

This is a web app and database developed as part of a Masters Engineering project at the University of Strathclyde. This should be active at em501-landslide-monitoring.azurewebsites.net (as of 22/4/22).

The app is written in Python Flask, and it manages a data stream from a landslide monitoring device at the Rest and Be Thankful landslide.
This data is formatted and stored in a Mongo database. The app also allows a user to view and download the data, and creates live plots of the newest data.

Also included is the code running on the Raspberry Pi of the remote monitoring device. This includes Startup.py, which checks if the Pi is connected to the internet, a sensing script (sense.py) which reads from an ADC and an upload script (Upload_TryExcept.py) which sends this to the webapp. These scripts should be run from boot, with Startup.py first and then sense.py and Upload_TryExcept.py run when Startup.py has finished. sense.py and Upload_TryExcept.py are designed to run simultaneously, with one recording and one sending respectively.

Requirements are included for both the webapp and the Raspberry Pi. For the Pi, some requirements are not available via pip install and will need to be downloaded manually. See Raspberry Pi code/requirements.txt for details.

## Licensing

Feel free to use any of the code for any purpose, as described by the GNU General Public License v3.0.

