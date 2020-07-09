#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, Response, jsonify, request
from jinja2 import Template
import json
import pigpio
from i2c import I2c
from motor import Motor
import time
from threading import Thread, Lock
import codecs
from collections import deque
import pymysql
import pymysql.cursors
import sys
import sqlite3
import datetime
values = deque(maxlen=1000)

pi=pigpio.pi()
i2cInstance = I2c(pi)
motor = Motor(pi)

#profiles = {'Rosemary': {'dry_value':10,'dry_time':3000,KETPmoy: ,KETPmax: }}


database_path = "/media/NAS/"

app= Flask(__name__)

d = datetime.datetime.now()
date = str(d.day)+"/"+str(d.month)+"/"+str(d.year)+" at "+str(d.hour)+":"+str(d.minute)+":"+str(d.second)

def poll_data(i2cCall,piCall):
        next=time.time()
	changed = False
	update = True
	delay = time.time()
        while True:
		now=time.time()
		mydbControl = sqlite3.connect(database_path+"controls.db")
                controlCursor = mydbControl.cursor()
		controlCursor.execute("SELECT variable,data from controls where variable = 'watering'")
		watering = controlCursor.fetchall()[0][1]
		sql = "REPLACE INTO controls(variable,data) VALUES(?,?)"
		if watering==1:
			if not changed:
				update = True
			if update :
				controlCursor.execute(sql,["next",time.time()+2])
				mydbControl.commit()
				changed = True
				update = False
		elif watering == 0:
			if changed:
				delay = time.time()+60
				changed = False
				update = True
			if now > delay :
				if update:
					controlCursor.execute(sql,["next",time.time()+599])
					mydbControl.commit()
					update = False
			elif now < delay :
				if update:
					#print(delay-now)
					controlCursor.execute(sql,["next",time.time()+2])
        	                        mydbControl.commit()
					update = False
		mydbControl.close()

		mydbControl = sqlite3.connect(database_path+"controls.db")
                controlCursor = mydbControl.cursor()
                controlCursor.execute("SELECT variable,data from controls where variable = 'next'")
                next = controlCursor.fetchall()[0][1]
                mydbControl.close()

		if now > next :
			update = True
			for device in i2cCall.devices: #we cover all the detected attinys
				#temps1=time.time()
	                       	read = i2cCall.read_sensor(device) #we read the sensor
				#print('tps1'+str(time.time()-temps1))
				#print(read)
        	               	nowread = time.time() #we read the time when the measurement was done
                	       	sql = "INSERT INTO hygrometry"+str(device)+" (time,measure) VALUES (?,?)"
                       		if read is not None:
					val = (nowread,read)
                        	       	values.append(val)
					mydb = sqlite3.connect(database_path+"measurements.db")
					measureCursor = mydb.cursor()
                        	       	measureCursor.execute(sql,val)
                        	       	mydb.commit()
					mydb.close()
					if read < i2cCall.threshold[str(device)]:
						if device not in i2cCall.dry_list:
							i2cCall.dry_list.append(device)
					elif read > i2cCall.threshold[str(device)]:
						if device in i2cCall.dry_list:
							del i2cCall.dry_list[i2cCall.dry_list.index(device)]
					else:
						pass
				#print('tps2'+str(time.time()-temps1))
				time.sleep(0.1)
		time.sleep(0.1)

def automatic(i2cCall, piCall, motorCall):
	while True :
		mydbControl = sqlite3.connect(database_path+"controls.db")
		controlCursor = mydbControl.cursor()
		controlCursor.execute("SELECT variable,data from controls where variable = 'mode'")
		mode = controlCursor.fetchall()[0][1]
		mydbControl.close()
		if mode == 1:
		        mydbControl = sqlite3.connect(database_path+"controls.db")
        		controlCursor = mydbControl.cursor()
        		controlCursor.execute("SELECT variable,data from controls where variable = 'threshold'")
        		threshold = controlCursor.fetchall()[0][1]
			mydbControl.close()

			mydb = sqlite3.connect(database_path+"measurements.db")
                        cursor = mydb.cursor()
			last_data = []
			for device in i2cCall.devices :
                        	cursor.execute("SELECT * FROM hygrometry"+str(device)+" ORDER BY time DESC LIMIT 1")
				data = cursor.fetchall()
				if len(data) != 0:
                        		last_data.append(data[0][1])
                        mydb.close()
			for device in i2cCall.devices :
				if len(last_data) == len(i2cCall.devices) :
					if last_data[i2cCall.devices.index(device)] < i2cCall.threshold[str(device)]:
						motorCall.water(500,2,10)
			#print(last_data)
			time.sleep(10)
			pass

		else:
			time.sleep(1)


@app.route("/<int:device>/data.json")
def data(device):
	mydb = sqlite3.connect(database_path+"measurements.db")
	showCursor = mydb.cursor()
	showCursor.execute("SELECT 1000*time, measure from hygrometry"+str(device))
        results = showCursor.fetchall()
	mydb.close()
        return json.dumps(results)

@app.route("/graph")
def graph():
	threshold=[]
	for device in i2cInstance.devices:
		threshold.append(i2cInstance.threshold[str(device)])
	#print(threshold)
        return render_template("graph.html", devices = i2cInstance.devices,watering = i2cInstance.watering, threshold = threshold, dry = i2cInstance.dry_list)


@app.route("/settings", methods = ['POST','GET'])
def settings():
	message=''
        mydbControl = sqlite3.connect(database_path+"controls.db")
        controlCursor = mydbControl.cursor()
        controlCursor.execute("SELECT variable,data from controls where variable = 'mode'")
	mode = controlCursor.fetchall()[0][1]
	mydbControl.close()
        if mode == 0:
                mode='Manual'
        elif mode == 1:
                mode ='Automatic'

	if request.method == 'GET':
		#i2cInstance.scan()
		if len(i2cInstance.watering) == 1:
		        i2cInstance.flow[str(i2cInstance.watering[0])] += motor.flow()

		flows = []
		flows.append(motor.flowr)
		threshold=[]
	        for device in i2cInstance.devices:
	                threshold.append(i2cInstance.threshold[str(device)])
			flows.append(i2cInstance.flow[str(device)])
                devices=i2cInstance.devices
                return render_template("settings.html", devices=devices, mode=mode, threshold=threshold, flows=flows, date = date)


	elif request.method == 'POST' :
		#change i2c address
		if 'ad_change' in request.form:
			f_adress = int(request.form["faddress"])
			n_adress = int(request.form["naddress"])
			i2cInstance.change_adress(f_adress,n_adress)
			message = "Changed adress "+ str(f_adress) +" to "+str(n_adress)
		#scan i2c addresses
		elif 'scan' in request.form:
			devicesBef=[]
			for device in i2cInstance.devices:
				devicesBef.append(device)
                    	i2cInstance.scan()
			devices=i2cInstance.devices
                        threshold = []
                        for device in i2cInstance.devices:
				threshold.append(i2cInstance.threshold[str(device)])

			if devicesBef != devices:
				#return render_template("select_profile.html")
				message = "New plant detected"
		#change mode to automatic
		elif 'Manual' in request.form:
			mydbControl = sqlite3.connect(database_path+"controls.db")
                	controlCursor = mydbControl.cursor()
			sql = "REPLACE INTO controls(variable,data) VALUES(?,?)"
                        controlCursor.execute(sql,["mode",1])
			mydbControl.commit()
			mydbControl.close()
			mode='Automatic'
		#change mode to manual
                elif 'Automatic' in request.form:
                        mydbControl = sqlite3.connect(database_path+"controls.db")
                        controlCursor = mydbControl.cursor()
                        sql = "REPLACE INTO controls(variable,data) VALUES(?,?)"
                        controlCursor.execute(sql,["mode",0])
                        mydbControl.commit()
                        mydbControl.close()
			mode='Manual'
		#change threshold
		elif 'change' in request.form:
			threshold = []
			for device in i2cInstance.devices:
				if len(request.form.get("threshold"+str(device))) > 0:
					i2cInstance.threshold[str(device)] = int(request.form.get("threshold"+str(device)))
                		threshold.append(i2cInstance.threshold[str(device)])
			#print(threshold)
		#request not implemented yet
		else:
			message = "Not implemented"
			print("not implemented")

                if len(i2cInstance.watering) == 1:
                         i2cInstance.flow[str(i2cInstance.watering[0])] += motor.flow()
                flows = []
                flows.append(motor.flowr)
		threshold=[]
                for device in i2cInstance.devices:
                        flows.append(i2cInstance.flow[str(device)])
			threshold.append(i2cInstance.threshold[str(device)])

		devices = i2cInstance.devices
		return render_template("settings.html", message=message, devices=devices, mode=mode, threshold=threshold, flows=flows, date=date)



@app.route("/<cmd>", methods = ['GET'])
def command(cmd=None):
	command=cmd.upper()
	if command[0:5] == 'WATER':
                mydbControl = sqlite3.connect(database_path+"controls.db")
		controlCursor = mydbControl.cursor()
		if command[6:9] == '_ON':
			if len(i2cInstance.watering) == 0:
				i2cInstance.On(int(command[5]))
			elif len(i2cInstance.watering) == 1:
				i2cInstance.flow[str(i2cInstance.watering[0])] += motor.flow()
				i2cInstance.Off(i2cInstance.watering[0])
				i2cInstance.On(int(command[5]))
			sql = "REPLACE INTO controls(variable,data) VALUES(?,?)"
			controlCursor.execute(sql,["watering",1])
			mydbControl.commit()
			mydbControl.close()
			#print(i2cInstance.watering)
			i2cInstance.flow[str(command[5])] += motor.turn(1000,1,1)
			return 'Watering '+command[5]
		elif command[6:10] == '_OFF':
			i2cInstance.flow[str(command[5])] += motor.flow()
			i2cInstance.flow[str(command[5])] += motor.off(1)
			i2cInstance.Off(int(command[5]))
			if len(i2cInstance.watering) == 1:
				del i2cInstance.watering[0]
			sql = "REPLACE INTO controls(variable,data) VALUES(?,?)"
			controlCursor.execute(sql,["watering",0])
			mydbControl.commit()
                        mydbControl.close()
			#print(i2cInstance.watering)
			return 'Stop watering '+command[5]
		else:
                        mydbControl.close()
			return 'Wrong command'
	else:
		print(command)
		return 'Command not implemented yet'



if __name__ == '__main__':
        try:
		i2cInstance.scan()
		mydb = sqlite3.connect(database_path+"measurements.db")
		measureCursor = mydb.cursor()
		for device in i2cInstance.devices:
			sql1 = "DROP TABLE IF EXISTS hygrometry"+str(device)
			measureCursor.execute(sql1)
			sql = "CREATE TABLE hygrometry"+str(device)+" (time INT, measure INT)"
			measureCursor.execute(sql)
		mydb.close()
                thr = Thread(target = poll_data, args=(i2cInstance,pi))
                thr.daemon = True
                thr.start()
		thr2 = Thread(target = automatic, args=(i2cInstance,pi,motor))
                thr2.daemon = True
                thr2.start()
                app.run(host='0.0.0.0', debug=False ,port=9090, threaded=True)

        except(KeyboardInterrupt):
		raise
	finally:
		if len(i2cInstance.watering) >0:
			i2cInstance.Off(i2cInstance.watering[0])
		mydb = sqlite3.connect(database_path+"controls.db")
		cursor = mydb.cursor()
		sql = "REPLACE INTO controls(variable,data) VALUES(?,?)"
                cursor.execute(sql,["watering",0])
		mydb.commit()
		mydb.close()

