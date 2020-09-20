#!/usr/bin/env python
# -*- coding: utf-8 -*-
from config import *
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


#database_path = "/media/NAS/"

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
        with sqlite3.connect(CONTROLS_LOGIN) as connection:
            controlCursor = connection.cursor()
        
        #mydbControl = sqlite3.connect(CONTROLS_LOGIN)
        #controlCursor = mydbControl.cursor()
            controlCursor.execute("SELECT variable,data from controls where variable = 'watering'")
            watering = controlCursor.fetchall()[0][1]
            if watering==1:
                if not changed:
                    update = True
                if update :
                    controlCursor.execute(UPDATE_CONTROLS,["next",time.time()+2])
                    connection.commit()
                    changed = True
                    update = False
            elif watering == 0:
                if changed:
                    delay = time.time()+60
                    changed = False
                    update = True
                if now > delay :
                    if update:
                        controlCursor.execute(UPDATE_CONTROLS,["next",time.time()+599])
                        connection.commit()
                        update = False
                elif now < delay :
                    if update:
                        controlCursor.execute(UPDATE_CONTROLS,["next",time.time()+2])
                        connection.commit()
                        update = False
        #mydbControl.close()

        #mydbControl = sqlite3.connect(CONTROLS_LOGIN)
        #controlCursor = mydbControl.cursor()
            controlCursor.execute("SELECT variable,data from controls where variable = 'next'")
            next = controlCursor.fetchall()[0][1]
        #mydbControl.close()

        if now > next :
            update = True
            for device in i2cCall.devices: #we cover all the detected attinys
                read = i2cCall.read_sensor(device) #we read the sensor
                nowread = time.time() #we read the time when the measurement was done
                sql = "INSERT INTO hygrometry"+str(device)+" (time,measure) VALUES (?,?)"
                if read is not None:
                    val = (nowread,read)
                    values.append(val)
                    mydb = sqlite3.connect(MEASUREMENTS_LOGIN)
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
                time.sleep(0.1)
        time.sleep(0.1)

def automatic(i2cCall, piCall, motorCall):
    while True :
        with sqlite3.connect(CONTROLS_LOGIN) as connection:
            controlCursor = connection.cursor()
        #mydbControl = sqlite3.connect(CONTROLS_LOGIN)
        #controlCursor = mydbControl.cursor()
            controlCursor.execute("SELECT variable,data from controls where variable = 'mode'")
            mode = controlCursor.fetchall()[0][1]
        #mydbControl.close()
            if mode == 1:
                #mydbControl = sqlite3.connect(CONTROLS_LOGIN)
                #controlCursor = mydbControl.cursor()
                controlCursor.execute("SELECT variable,data from controls where variable = 'threshold'")
                i2cCall.threshold = controlCursor.fetchall()[0][1]
                #mydbControl.close()
                
                with sqlite3.connect(MEASUREMENTS_LOGIN) as connection2:
                    cursor = connection2.cursor()
                #mydb = sqlite3.connect(MEASUREMENTS_LOGIN)
                #cursor = mydb.cursor()
                    last_data = []
                    for device in i2cCall.devices :
                        cursor.execute("SELECT * FROM hygrometry"+str(device)+" ORDER BY time DESC LIMIT 1")
                        data = cursor.fetchall()
                        if len(data) != 0:
                            last_data.append(data[0][1])
                #mydb.close()
                for device in i2cCall.devices :
                    if len(last_data) == len(i2cCall.devices) :
                        if last_data[i2cCall.devices.index(device)] < i2cCall.threshold[str(device)]:
                            motorCall.water(500,2,10)
                time.sleep(10)
                pass

            else:
                time.sleep(1)


@app.route("/<int:device>/data.json")
def data(device):
    with sqlite3.connect(MEASUREMENTS_LOGIN) as connection:
        showCursor = connection.cursor()
    #mydb = sqlite3.connect(MEASUREMENTS_LOGIN)
    #showCursor = mydb.cursor()
        showCursor.execute("SELECT 1000*time, measure from hygrometry"+str(device))
        results = showCursor.fetchall()
    #mydb.close()
        return json.dumps(results)

@app.route("/graph")
def graph():
    threshold=[]
    for device in i2cInstance.devices:
        threshold.append(i2cInstance.threshold[str(device)])
    return render_template("graph.html", devices = i2cInstance.devices,watering = i2cInstance.watering, threshold = threshold, dry = i2cInstance.dry_list)


@app.route("/settings", methods = ['POST','GET'])
def settings():
    message=''
    with sqlite3.connect(CONTROLS_LOGIN) as connection:
        controlCursor = connection.cursor()
    #mydbControl = sqlite3.connect(CONTROLS_LOGIN)
    #controlCursor = mydbControl.cursor()
        controlCursor.execute("SELECT variable,data from controls where variable = 'mode'")
        mode = controlCursor.fetchall()[0][1]
    #mydbControl.close()
    if mode == 0:
        mode='Manual'
    elif mode == 1:
        mode ='Automatic'

    if request.method == 'GET':
        flows = []
        if len(i2cInstance.watering) == 1:
            i2cInstance.flow[str(i2cInstance.watering[0])] += motor.flow()
            flows.append(motor.flowr)

        threshold = []
        for device in i2cInstance.devices:
            flows.append(i2cInstance.flow[str(device)])
            devices=i2cInstance.devices
            threshold.append(i2cInstance.threshold[str(device)])

        return render_template("settings.html", devices=devices, mode=mode, threshold=threshold, flows=flows, date = date)


    elif request.method == 'POST' :
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
            with sqlite3.connect(CONTROLS_LOGIN) as connection:
                controlCursor = connection.cursor()
            #mydbControl = sqlite3.connect(CONTROLS_LOGIN)
            #controlCursor = mydbControl.cursor()
                controlCursor.execute(UPDATE_CONTROLS,["mode",1])
                connection.commit()
            #mydbControl.commit()
            #mydbControl.close()
            mode='Automatic'
        #change mode to manual
        elif 'Automatic' in request.form:
            with sqlite3.connect(CONTROLS_LOGIN) as connection:
                controlCursor = connection.cursor()
            #mydbControl = sqlite3.connect(CONTROLS_LOGIN)
            #controlCursor = mydbControl.cursor()
                controlCursor.execute(UPDATE_CONTROLS,["mode",0])
                connection.commit()
            #mydbControl.commit()
            #mydbControl.close()
            mode='Manual'
        #change threshold
        elif 'change' in request.form:
            threshold = []
            for device in i2cInstance.devices:
                if len(request.form.get("threshold"+str(device))) > 0:
                    i2cInstance.threshold[str(device)] = int(request.form.get("threshold"+str(device)))
                    threshold.append(i2cInstance.threshold[str(device)])
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
        with sqlite3.connect(CONTROLS_LOGIN) as connection:
            controlCursor = connection.cursor()
        #mydbControl = sqlite3.connect(CONTROLS_LOGIN)
        #controlCursor = mydbControl.cursor()
            if command[6:9] == '_ON':
                if len(i2cInstance.watering) == 0:
                    print(command[5])
                    i2cInstance.On(int(command[5]))
                elif len(i2cInstance.watering) == 1:
                    i2cInstance.flow[str(i2cInstance.watering[0])] += motor.flow()
                    i2cInstance.Off(i2cInstance.watering[0])
                    i2cInstance.On(int(command[5]))
                controlCursor.execute(UPDATE_CONTROLS,["watering",1])
                connection.commit()
                #mydbControl.commit()
                #mydbControl.close()
                i2cInstance.flow[str(command[5])] += motor.turn(1000,1,1)
                return 'Watering '+command[5]
            elif command[6:10] == '_OFF':
                i2cInstance.flow[str(command[5])] += motor.flow()
                i2cInstance.flow[str(command[5])] += motor.off(1)
                i2cInstance.Off(int(command[5]))
                if len(i2cInstance.watering) == 1:
                    del i2cInstance.watering[0]
                controlCursor.execute(UPDATE_CONTROLS,["watering",0])
                connection.commit()
                #mydbControl.commit()
                #mydbControl.close()
                return 'Stop watering '+command[5]
            else:
                #mydbControl.close()
                return 'Wrong command'
    else:
        print(command)
        return 'Command not implemented yet'



if __name__ == '__main__':
    try:
        i2cInstance.scan()
        if sys.argv[1] == 'y':
            with sqlite3.connect(MEASUREMENTS_LOGIN) as connection:
                measureCursor = connection.cursor()
        #mydb = sqlite3.connect(MEASUREMENTS_LOGIN)
        #measureCursor = mydb.cursor()
                for device in i2cInstance.devices:
                    sql_drop = "DROP TABLE IF EXISTS hygrometry"+str(device)
                    measureCursor.execute(sql_drop)
                    #sql = "CREATE TABLE hygrometry"+str(device)+" (time INT, measure INT)"
                    sql = HYGROMETRY_TABLE.format("hygrometry"+str(device))
                    measureCursor.execute(sql)
            with sqlite3.connect(CONTROLS_LOGIN) as connection:
                controlsCursor = connection.cursor()
                sql_drop = "DROP TABLE IF EXISTS controls"
                controlsCursor.execute(sql_drop)
                controlsCursor.execute(CONTROLS_TABLE)
		controlsCursor.execute(FILL_CONTROLS)
		connection.commit()
            #mydb.close()
        thr = Thread(target = poll_data, args=(i2cInstance,pi))
        thr.daemon = True
        thr.start()
        thr2 = Thread(target = automatic, args=(i2cInstance,pi,motor))
        thr2.daemon = True
        thr2.start()
        app.run(**FLASK_CONFIG)

    except(KeyboardInterrupt):
        raise
    finally:
        if len(i2cInstance.watering) >0:
            i2cInstance.Off(i2cInstance.watering[0])
        with sqlite3.connect(CONTROLS_LOGIN) as connection:
            cursor = connection.cursor()
        #mydb = sqlite3.connect(CONTROLS_LOGIN)
        #cursor = mydb.cursor()
            cursor.execute(UPDATE_CONTROLS,["watering",0])
            connection.commit()
        #mydb.commit()
        #mydb.close()

