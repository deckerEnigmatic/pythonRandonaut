#!/usr/bin/python
# EngimaticDevices.com 2020
# Randonauts script - generate geo coordinates
# from a HWRNG


from __future__ import division
from math import radians, cos, sin, asin, sqrt
import numpy as np
import sendSMS
import subprocess
import sys
import time
import json
import urllib2
from time import strftime
import orbitalWrite

# haversine function to determine distance between two lat,long points
def haversine(lat1, lon1, lat2, lon2):
	R = 3959.87433 #earth radius in miles
	dLat = radians(lat2 - lat1)
	dLon = radians(lon2 - lon1)
	a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
	c = 2*asin(sqrt(a))
	return R*c

# get a random number from a hardware random number generator
# there are also public RNG APIs available
def getfloat():

	getnum = json.load(urllib2.urlopen("http://"+HWRNG+"/rangeFloat"))
	output = getnum[0]["value"]
	return output

def str_time_prop(start, end, format, prop):
	#get a time at a proportion of a range of two formatted times
	stime = start
	etime = end
	ptime = stime + prop * (etime - stime)

	return time.strftime(format, time.localtime(ptime))

# get random time in the future
def random_date(start, end, prop):
	return str_time_prop(start, end, '%m/%d/%Y %I:%M%p', prop)

# function to generate a lat,long coordinate within a range
# inspiration from this post:
# https://gis.stackexchange.com/questions/25877/generating-random-locations-nearby
def create_random_point(x0,y0,distance):
	#approximately 1609 meters in a mile
	#5 miles = about 8045
        # 111300 = meters in a degree
        # 69 = miles in a degree
        r = distance / 111300
	r = r/2
	u = float(getfloat())
	v = float(getfloat())
        w = r * np.sqrt(u)
        t = 2 * np.pi * v
        x = w * np.cos(t)
        x1 = x / np.cos(y0)
        y = w * np.sin(t)
        print "u="+str(u)
        print "v="+str(v)
        return (x0+x1, y0+y)


init_start = time.time()
dtime = strftime("%m-%d-%Y %H:%M:%S")
newplot = ()

##### User defined variables #####

loghandle = '/tmp/rabbit.log'
logfile = open(loghandle, "a")

#home_base (starting point)
latitude1, longitude1 = 28.385573,-81.563853

# mobile number for SMS text
# ex. 15551212
to_num = '1XXXXXXX'

#window_secs = 10800
window_secs = 1800 

#how far to travel in meters from home base
meters_out = 4827 

#lcd_addr - the address of the display if using I2C
lcd_addr = 0x5C

#HWRNG Server IP and Port
HWRNG = '192.168.1.133:5000'

##### End User Defined variables #####

current_time = time.time()
window = current_time + window_secs
orbitalWrite.clear_display(lcd_addr)

# for loop to get multiple points if desired (for future development - void/attractor calculations)
for i in range(1,2):
	timex = float(getfloat())
        x,y = create_random_point(latitude1,longitude1, meters_out)
	future_time = random_date(current_time, window, timex)
	dest_lat = str(format(x,'.5f'))
	dest_long = str(format(y,'.5f'))
	orig_lat = str(latitude1)
	orig_long = str(longitude1)
        newplot = (x,y)
        origplot = (latitude1,longitude1)
        dist = haversine(origplot[0],origplot[1],newplot[0],newplot[1])
	dist = str(format(dist,'.2f'))
        print "Distance between points is ",dist
	print "destination: "+dest_lat+" "+dest_long
	print "future_time: "+future_time
	logfile.write(dtime+" homebase_lat="+orig_lat+" homebase_long="+orig_long+" dest_lat="+dest_lat+" dest_long="+dest_long+" future_time="+future_time+" dist="+dist)

	msg_breaker = '~'
	msg_space = '`'
	msg_space2 = '```'
	#homage to the Matrix
	init1_msg = 'Wake up, Neo...'
	init_msg = 'The Matrix has you..'
	rabbit_msg1 = 'follow the'
	rabbit_msg2 = 'white rabbit...'

	logfile.write("\n")
	orbitalWrite.write_display(lcd_addr,init1_msg)
	time.sleep(5)
	orbitalWrite.clear_display(lcd_addr)
	orbitalWrite.write_display(lcd_addr,msg_breaker)
	orbitalWrite.write_display(lcd_addr,init_msg)
	time.sleep(5)
	orbitalWrite.clear_display(lcd_addr)
	orbitalWrite.write_display(lcd_addr,msg_breaker)
	orbitalWrite.write_display(lcd_addr,rabbit_msg1)
	orbitalWrite.write_display(lcd_addr,msg_breaker)
	orbitalWrite.write_display(lcd_addr,msg_space2)
	orbitalWrite.write_display(lcd_addr,rabbit_msg2)
	time.sleep(5)
	orbitalWrite.clear_display(lcd_addr)
	orbitalWrite.write_display(lcd_addr,msg_breaker)
	orbitalWrite.write_display(lcd_addr," "+future_time)
	orbitalWrite.write_display(lcd_addr,msg_breaker)
	orbitalWrite.write_display(lcd_addr," "+dest_lat)
	orbitalWrite.write_display(lcd_addr,msg_space)
	orbitalWrite.write_display(lcd_addr,dest_long)
	#clear display after x seconds
	time.sleep(120)

	orbitalWrite.clear_display(lcd_addr)

#Send a map link via Twilio SMS
sendSMS.send_sms(to_num, dest_lat, dest_long, future_time)
