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
import sqlite3

values = deque(maxlen=1000)
#lock = Lock()
#watering = False
#next = 0
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


#mydb = sqlite3.connect('measurements.db')
#mydb = pymysql.connect(
#	host = 'localhost',
#        user = str(sys.argv[1]),
#        passwd = str(sys.argv[2]),
#        database = 'measurements'
#)


#mydbControl = pymysql.connect(
#        host = 'localhost',
#        user = str(sys.argv[1]),
#        passwd = str(sys.argv[2]),
#        database = 'controls'
#)

#measureCursor = mydb.cursor()
#showCursor = mydb.cursor()
#controlCursor = mydbControl.cursor()
#next = 0


app= Flask(__name__)


def poll_data(i2cCall,piCall,inputCursor):
        next=time.time()
	#global watering
	#global next
        while True:
		#print watering
		now=time.time()
		mydbControl = pymysql.connect(
		        host = 'localhost',
        		user = str(sys.argv[1]),
        		passwd = str(sys.argv[2]),
        		database = 'controls'
		)
		controlCursor = mydbControl.cursor()
		controlCursor.execute("SELECT variable,data from controls where variable = 'next'")
		next = controlCursor.fetchall()[0][1]
		mydbControl.close()
		#print(next)
                if now>next:
			mydbControl = pymysql.connect(
	                        host = 'localhost',
        	                user = str(sys.argv[1]),
                	        passwd = str(sys.argv[2]),
                	        database = 'controls'
                	)
                	controlCursor = mydbControl.cursor()
			controlCursor.execute("SELECT variable,data from controls where variable = 'watering'")
			watering = controlCursor.fetchall()[0][1]
			print(watering)
			sql = "REPLACE INTO controls(variable,data) VALUES(%s,%s)"
			if watering==1:
				controlCursor.execute(sql,["next",time.time()+2])
				mydbControl.commit()
			#	lock.acquire()
			#	next = time.time() +9.5
			#	lock.release()
			else:
				controlCursor.execute(sql,["next",time.time()+599])
				mydbControl.commit()
			#	lock.acquire()
			#next = time.time()+9
			#	lock.release()
			mydbControl.close()
			for device in i2cCall.devices: #we cover all the detected attinys
				#temps1=time.time()
	                       	read = i2cCall.read_sensor(device) #we read the sensor
				#print('tps1'+str(time.time()-temps1))
				#print(read)
        	               	nowread = time.time() #we read the time when the measurement was done
                	       	sql = "INSERT INTO hygrometry"+str(device)+" (time,measure) VALUES (%s,%s)"
                       		if read is not None:
					val = (nowread,read)
                        	       	values.append(val)
					mydb = pymysql.connect(
					        host = 'localhost',
        					user = str(sys.argv[1]),
        					passwd = str(sys.argv[2]),
        					database = 'measurements'
					)
					measureCursor = mydb.cursor()
                        	       	measureCursor.execute(sql,val)
                        	       	mydb.commit()
					mydb.close()
				#print('tps2'+str(time.time()-temps1))
				time.sleep(0.1)
		time.sleep(0.1)

@app.route("/<int:device>/data.json")
def data(device):
	mydb = pymysql.connect(
        	host = 'localhost',
        	user = str(sys.argv[1]),
        	passwd = str(sys.argv[2]),
        	database = 'measurements'
	)
	showCursor = mydb.cursor()
	showCursor.execute("SELECT 1000*time, measure from hygrometry"+str(device))
        results = showCursor.fetchall()
	mydb.close()
	#print(results)
	#mydb.close()
#	results = list(results)
#	results.insert(0,('time','value'))
#	print(results)
        return json.dumps(results)

@app.route("/graph")
def graph():
        return render_template("graph.html", devices = i2cInstance.devices,watering = i2cInstance.watering)
#, watering= watering)

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
	#global watering
	#global next
	if command[0:5] == 'WATER':
                mydbControl = pymysql.connect(
                        host = 'localhost',
                        user = str(sys.argv[1]),
                        passwd = str(sys.argv[2]),
                        database = 'controls'
                )
		controlCursor = mydbControl.cursor()
		if command[6:9] == '_ON':
			if len(i2cInstance.watering) == 0:
				i2cInstance.On(int(command[5]))
			elif len(i2cInstance.watering) == 1:
				i2cInstance.Off(i2cInstance.watering[0])
				i2cInstance.On(int(command[5]))
			sql = "REPLACE INTO controls(variable,data) VALUES(%s,%s)"
			controlCursor.execute(sql,["watering",1])
			controlCursor.execute(sql,["next",time.time()+2])
			#lock.acquire()
			#watering = True
			#next = time.time() + 1
			#lock.release()
			mydbControl.commit()
			mydbControl.close()
			print(i2cInstance.watering)
			return 'Watering '+command[5]
		elif command[6:10] == '_OFF':
			i2cInstance.Off(int(command[5]))
			if len(i2cInstance.watering) == 1:
				del i2cInstance.watering[0]
			sql = "REPLACE INTO controls(variable,data) VALUES(%s,%s)"
			controlCursor.execute(sql,["watering",0])
			controlCursor.execute(sql,["next",time.time()+599])
			mydbControl.commit()
                        mydbControl.close()
			#lock.acquire()
			#watering = False
			#next = time.time() + 359
			#lock.release()
			print(i2cInstance.watering)
			return 'Stop watering '+command[5]
		else:
                        mydbControl.close()
			return 'Wrong command'
	else:
		return 'Command not implemented yet' 
		#i2cInstance.write(0x4,0xC2)
		#i2cInstance.write(0x4,255)


if __name__ == '__main__':
        try:
		i2cInstance.scan()
		mydb = pymysql.connect(
		        host = 'localhost',
		        user = str(sys.argv[1]),
		        passwd = str(sys.argv[2]),
		        database = 'measurements'
		)
		measureCursor = mydb.cursor()
		for device in i2cInstance.devices:
			sql1 = "DROP TABLE IF EXISTS hygrometry"+str(device)
			measureCursor.execute(sql1)
			sql = "CREATE TABLE hygrometry"+str(device)+" (time INT, measure INT)"
			measureCursor.execute(sql)
		mydb.close()
                thr = Thread(target = poll_data, args=(i2cInstance,pi,measureCursor))
                thr.daemon = True
                thr.start()
                app.run(host='0.0.0.0', debug=False ,port=9090, threaded=True)

        except(KeyboardInterrupt):
		raise
	finally:
		if len(i2cInstance.watering) >0:
			i2cInstance.Off(i2cInstance.watering[0])
		mydb = pymysql.connect(
                        host = 'localhost',
                        user = str(sys.argv[1]),
                        passwd = str(sys.argv[2]),
                        database = 'controls'
                )
		cursor = mydb.cursor()
		sql = "REPLACE INTO controls(variable,data) VALUES(%s,%s)"
                cursor.execute(sql,["watering",0])
		mydb.commit()
		mydb.close()
		#mydb.close()
		#mydbControl.close()


