#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, Response, jsonify, request
from jinja2 import Template
import json
import pigpio
from i2c import I2c
import time
from threading import Thread, Lock
import codecs
from collections import deque
import pymysql
import pymysql.cursors
import sys

values = deque(maxlen=1000)
#lock = Lock()
watering = False
next = 0
#WATER4_ON = "water4_on"
#WATER4_OFF = "water4_off"

#AVAILABLE_COMMANDS = {
#	'Water4_ON' : WATER4_ON
#	'Water4_OFF' : WATER4_OFF
#}

pi=pigpio.pi()
pi.set_mode(23,pigpio.INPUT)
pi.set_pull_up_down(23,pigpio.PUD_UP)
i2cInstance = I2c(pi)

mydb = pymysql.connect(
	host = 'localhost',
        user = str(sys.argv[1]),
        passwd = str(sys.argv[2]),
        database = 'measurements'
)
mycursor = mydb.cursor()
cursor = mydb.cursor()
#next = 0

app= Flask(__name__)


def poll_data(i2cCall,piCall,sqlCursor):
        next=time.time()
	#global watering
	#global next
        while True:
		#print watering
		now=time.time()
                if now>next:
			#if watering:
			#	lock.acquire()
			#	next = time.time() +9.5
			#	lock.release()
			#else:
			#	lock.acquire()
			next = time.time()+9.9
			#	lock.release()
			for device in i2cCall.devices: #we cover all the detected attinys
	                       	read = i2cCall.read_sensor(device) #we read the sensor
        	               	nowread = time.time() #we read the time when the measurement was done
                	       	sql = "INSERT INTO hygrometry"+str(device)+" (time,measure) VALUES (%s,%s)"
                       		if read is not None:
					val = (nowread,read)
                        	       	values.append(val)
                        	       	sqlCursor.execute(sql,val)
                        	       	mydb.commit()
				time.sleep(0.1)


@app.route("/<int:device>/data.json")
def data(device):
	cursor.execute("SELECT 1000*time, measure from hygrometry"+str(device))
        results = cursor.fetchall()
	#mydb.close()
        return json.dumps(results)

@app.route("/graph")
def graph():
        return render_template("graph.html", devices = i2cInstance.devices)

#@app.route("/settings")
#def index():
#	return render_template("settings.html")

@app.route("/settings", methods = ['POST','GET'])
def settings():
	message=''
	bar=[]
	if request.method == 'POST' :
		if 'submit' in request.form:
			f_adress = int(request.form["faddress"])
			n_adress = int(request.form["naddress"])
			i2cInstance.change_adress(f_adress,n_adress)
			message = "Changed adress "+ str(f_adress) +" to "+str(n_adress)
		if 'scan' in request.form:
                    	i2cInstance.scan()
			bar=i2cInstance.devices
		return render_template("settings.html", message=message, foobar=bar)
	else :
		return render_template("settings.html")

@app.route("/<cmd>", methods = ['GET'])
def command(cmd=None):
	command=cmd.upper()
	#return command[0:5]
	global watering
	global next
	if command[0:5] == 'WATER':
		if command[6:9] == '_ON':
			i2cInstance.On(int(command[5]))
			#lock.acquire()
			#watering = True
			#next = time.time() + 1
			#lock.release()
			return 'Watering '+command[5]
		elif command[6:10] == '_OFF':
			i2cInstance.Off(int(command[5]))
			#lock.acquire()
			#watering = False
			#next = time.time() + 359
			#lock.release()
			return 'Stop watering '+command[5]
		else:
			return 'Wrong command'
	else:
		return 'Command not implemented yet' 
		#i2cInstance.write(0x4,0xC2)
		#i2cInstance.write(0x4,255)


if __name__ == '__main__':
        try:
		i2cInstance.scan()
		for device in i2cInstance.devices:
			sql1 = "DROP TABLE IF EXISTS hygrometry"+str(device)
			mycursor.execute(sql1)
			sql = "CREATE TABLE hygrometry"+str(device)+" (time INT, measure INT)"
			mycursor.execute(sql)
                thr = Thread(target = poll_data, args=(i2cInstance,pi,mycursor))
                thr.daemon = True
                thr.start()

                app.run(host='0.0.0.0', debug=False ,port=9090, threaded=True)

        except(KeyboardInterrupt):
                mydb.close()
                raise


