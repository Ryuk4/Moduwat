#!/usr/bin/env python -*- coding: utf-8 -*-
from config import *
from flask import Flask, render_template, Response, jsonify, request
from jinja2 import Template
import json
import pigpio
from i2c import I2c
from motor import Motor
import time
from threading import Thread
import sys
import sqlite3
import datetime
from flask_cors import cross_origin
import pytz
from gevent.pywsgi import WSGIServer
import os

pi=pigpio.pi()
i2cInstance = I2c(pi)
motor = Motor(pi)


app= Flask(__name__)

http_server = WSGIServer(('', 9090), app)


d = pytz.utc.localize(datetime.datetime.now())
date = str(d.day)+"/"+str(d.month)+"/"+str(d.year)+" at "+str(d.hour)+":"+str(d.minute)+":"+str(d.second)

def poll_data(i2cCall, piCall):
    next=time.time()
    changed = False
    reading = True
    delay = time.time()
    while True:
        now=time.time()
        with sqlite3.connect(CONTROLS_LOGIN, timeout=10) as connection:
            controlCursor = connection.cursor()
            controlCursor.execute("SELECT variable,data from controls where variable = 'watering'")
            watering = controlCursor.fetchall()[0][1]
            if watering == 1:
                if not changed:
                    reading = True
                if reading :
                    controlCursor.execute(UPDATE_CONTROLS,["next",time.time()+1.9])
                    connection.commit()
                    changed = True
                    reading = False
            elif watering == 0:
                if changed:
                    delay = time.time()+60
                    changed = False
                    reading = True

            if now > delay :
                if reading:
                    controlCursor.execute(UPDATE_CONTROLS,["next",time.time()+599.9])
                    connection.commit()
                    reading = False
            elif now < delay :
                if reading:
                    controlCursor.execute(UPDATE_CONTROLS,["next",time.time()+1.9])
                    connection.commit()
                    reading = False

        with sqlite3.connect(CONTROLS_LOGIN,timeout=10) as connection:
            controlCursor = connection.cursor()
            controlCursor.execute("SELECT variable,data from controls where variable = 'next'")
            next = controlCursor.fetchall()[0][1]

        if now > next :
            reading = True
            for device in i2cCall.devices: #we cover all the detected attinys
                read = i2cCall.read_sensor(device) #we read the sensor
                nowread = time.time() #we read the time when the measurement was done
                sql = "INSERT INTO hygrometry"+str(device)+" (time,measure) VALUES (?,?)"

                if read is not None:
                    val = (nowread,read)
                    with sqlite3.connect(MEASUREMENTS_LOGIN, timeout=10) as connection:
                        measureCursor = connection.cursor()
                        measureCursor.execute(sql,val)
                        connection.commit()

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

def automatic(i2cCall, piCall,  motorCall):
    while True :
        for device in i2cCall.devices:
            if i2cCall.mode[str(device)] == "Automatic":
                with sqlite3.connect(MEASUREMENTS_LOGIN,timeout=10) as connection2:
                    cursor = connection2.cursor()
                    last_data = {}
                    for device in i2cCall.devices :
                        cursor.execute("SELECT 1000*time, measure from hygrometry"+str(device))
                        data = cursor.fetchall()
                        if len(data) != 0:
                            #print data
                            last_data[str(device)] = data[-1][1]
                #print(last_data)
                if len(last_data) == len(i2cCall.devices) :
                    if last_data[str(device)] < i2cCall.threshold[str(device)]:
                        if (pytz.utc.localize(datetime.datetime.now()).hour >10 and pytz.utc.localize(datetime.datetime.now()).hour <12 ) or ( pytz.utc.localize(datetime.datetime.now()).hour >18 and pytz.utc.localize(datetime.datetime.now()).hour <21 ) :
                            with sqlite3.connect(CONTROLS_LOGIN,timeout=10) as connection:
                                controlCursor = connection.cursor()
                                controlCursor.execute(UPDATE_CONTROLS,["watering",1])
                                connection.commit()

                            i2cCall.On(device)
                            with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
                                cursor = connection.cursor()
                                sql = "SELECT Kc FROM plants WHERE plant = '"+i2cCall.plant_type[str(device)]+"'"
                                cursor.execute(sql)
                                Kc = cursor.fetchall()[0][0]
                            flow = Kc*ETP_CONFIG[datetime.date.today().month-1]
                            motorCall.water(500,2,flow)
                            i2cCall.Off(device)
                            i2cCall.flow[str(device)] += flow
                            with sqlite3.connect(CONTROLS_LOGIN,timeout=10) as connection:
                                controlCursor = connection.cursor()
                                controlCursor.execute(UPDATE_CONTROLS,["watering",0])
                                connection.commit()
        time.sleep(1200)


@app.route("/<int:device>/data.json")
@cross_origin()
def data(device):
    with sqlite3.connect(MEASUREMENTS_LOGIN,timeout=10) as connection:
        showCursor = connection.cursor()
        showCursor.execute("SELECT 1000*time, measure from hygrometry"+str(device))
        results = showCursor.fetchall()
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
    edit=0
    with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
        cursor = connection.cursor()
        sql = "SELECT plant FROM plants"
        cursor.execute(sql)
        plants = cursor.fetchall()
    
    with sqlite3.connect(CONTROLS_LOGIN, timeout=10) as connection:
        cursor = connection.cursor()
        sql = "SELECT Id, start, stop FROM hours"
        cursor.execute(sql)
        hours = cursor.fetchall()
    
    plant_list = [str(sorted(plants)[x][0]) for x in range(len(plants))]
    hours = [[str(param[j]) for j in range(len(hours[0]))] for param in hours]
    #print(plant_list)
    if request.method == 'GET':
        flows = []
        if len(i2cInstance.watering) == 1:
            i2cInstance.flow[str(i2cInstance.watering[0])] += motor.flow()
        flows.append(motor.flowr)
        threshold = []
        mode = []
        devices = []
        preselected_id = []
        for device in i2cInstance.devices:
            flows.append(i2cInstance.flow[str(device)])
            threshold.append(i2cInstance.threshold[str(device)])
            devices.append(device)
            if i2cInstance.plant_type[str(device)] != "Select":
                preselected_id.append(plant_list.index(i2cInstance.plant_type[str(device)]))
            else:
                preselected_id.append(None)
            if i2cInstance.mode[str(device)] == "Manual":
                mode.append(0)
            if i2cInstance.mode[str(device)] == "Automatic":
                mode.append(1)

        return render_template("settings.html", devices=devices, mode=mode, threshold=threshold, flows=flows, date = date, plants = plant_list, preselected_plant=json.dumps(preselected_id), hours=hours, edit=edit)


    elif request.method == 'POST' :
        print(request.form)
        #change plant type
        for device in i2cInstance.devices:
            id_select="select"+str(device)
            if id_select in request.form:
                #print(id_select)
                select = request.form.get(id_select)
                selected = id_select[-1]
                i2cInstance.plant_type[str(device)] = select
                with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
                    cursor = connection.cursor()
                    sql = "SELECT dry FROM plants WHERE plant = '" + select + "'"
                    cursor.execute(sql)
                    Kc = cursor.fetchall()[0][0]
                #print(Kc)
                i2cInstance.threshold[str(device)] = 100*Kc
        #change mode
        for device in i2cInstance.devices:
            mode="mode"+str(device)
            if mode in request.form:
                print(mode)
                if i2cInstance.mode[str(device)] == "Manual":
                    i2cInstance.mode[str(device)] = "Automatic"
                elif i2cInstance.mode[str(device)] == "Automatic":
                    i2cInstance.mode[str(device)] = "Manual"

        #change adress of device
        if 'ad_change' in request.form:
            print(request.form)
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
            if len(devicesBef) < len(devices):
                message = "New plant detected"
                
        #if hour parameters modified and validated
        for hour in hours:
            if "ok"+hour[0] in request.form:
                if str(request.form["start"]) != "":
                    print(str(request.form["start"]))
                    hours[int(hour[0])-1][1] = str(request.form["start"])
                if str(request.form["stop"]) != "":
                    print(str(request.form["stop"]))
                    hours[int(hour[0])-1][2] = str(request.form["stop"])
                with sqlite3.connect(CONTROLS_LOGIN, timeout=10) as connection:
                    cursor = connection.cursor()
                    sql = "REPLACE INTO hours (Id,start,stop) VALUES(?,?,?)"
                    cursor.execute(sql,hours[int(hour[0])-1])
                    connection.commit()
        
        #if hour parameters changes are canceled
        if "cancel" in request.form:
            pass
        
        #if new line of hour parameters
        if "addline" in request.form:
            param = []
            if str(request.form["start"]) != "" and str(request.form["stop"]) != "" :
                print(str(request.form["start"]))
                param.append(str(request.form["start"]))
                print(str(request.form["stop"]))
                param.append(str(request.form["stop"]))
                print(param)
                with sqlite3.connect(CONTROLS_LOGIN, timeout=10) as connection:
                    cursor = connection.cursor()
                    sql = "INSERT INTO hours (start,stop) VALUES(?,?)"
                    cursor.execute(sql,param)
                    connection.commit()

        #if request for plant parameters edition or removal
        for hour in hours:
            if "edit"+str(hour[0]) in request.form:
                edit = hour[0]
            if "remove"+str(hour[0]) in request.form:
                with sqlite3.connect(CONTROLS_LOGIN, timeout=10) as connection:
                    cursor = connection.cursor()
                    sql = "DELETE FROM hours WHERE Id = '" + str(hour[0]) + "'"
                    cursor.execute(sql)
                    connection.commit()

    flows = []
    if len(i2cInstance.watering) == 1:
        i2cInstance.flow[str(i2cInstance.watering[0])] += motor.flow()
    flows.append(motor.flowr)
    threshold=[]
    mode = []
    devices = []
    preselected_id = []
    for device in i2cInstance.devices:
        flows.append(i2cInstance.flow[str(device)])
        threshold.append(i2cInstance.threshold[str(device)])
        devices.append(device)
        if i2cInstance.mode[str(device)] == "Manual":
            mode.append(0)
        if i2cInstance.mode[str(device)] == "Automatic":
            mode.append(1)
        if i2cInstance.plant_type[str(device)] != "Select":
            preselected_id.append(plant_list.index(i2cInstance.plant_type[str(device)]))
        else:
            preselected_id.append(None)

    return render_template("settings.html", message=message, devices=devices, mode=mode, threshold=threshold, flows=flows, date=date, plants = plant_list,preselected_plant=json.dumps(preselected_id), hours=hours,edit=edit)



@app.route("/<cmd>", methods = ['GET'])
def command(cmd=None):
    command=cmd.upper()
    if command[0:5] == 'WATER':
        with sqlite3.connect(CONTROLS_LOGIN,timeout=10) as connection:
            controlCursor = connection.cursor()
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

                return 'Stop watering '+command[5]
            else:
                return 'Wrong command'
    else:
        print(command)
        return 'Command not implemented yet'

@app.route("/database", methods = ['POST','GET'])
def show_database():
    edit=""
    if request.method == 'GET':
        with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
            cursor = connection.cursor()
            sql = "SELECT plant, Kc, dry, sun FROM plants ORDER BY plant ASC"
            cursor.execute(sql)
            plants = cursor.fetchall()
        #print(plants)
        plants = [[str(param[j]) for j in range(len(plants[0]))] for param in plants]
        return render_template("database.html",plants = plants,edit=json.dumps(edit))

    elif request.method == 'POST' :
        with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
            cursor = connection.cursor()
            sql = "SELECT plant, Kc, dry, sun FROM plants ORDER BY plant ASC"
            cursor.execute(sql)
            plants = cursor.fetchall()
        plants = [[str(param[j]) for j in range(len(plants[0]))] for param in plants]
        print(request.form)
        
        #if plant parameters modified and validated
        for plant in plants:
            if "ok"+plant[0] in request.form:
                index = plants.index(plant)
                if str(request.form["plant"]) != "":
                    print(str(request.form["plant"]))
                    plants[plants.index(plant)][0] = str(request.form["plant"])
                if str(request.form["Kc"]) != "":
                    print(str(float(request.form["Kc"])))
                    plants[plants.index(plant)][1] = float(request.form["Kc"])
                if str(request.form["threshold"]) != "":
                    print(str(float(request.form["threshold"])))
                    plants[plants.index(plant)][2] = float(request.form["threshold"])
                if str(request.form["sun"]) != "":
                    print(str(request.form["sun"]))
                    plants[plants.index(plant)][3] = str(request.form["sun"])
                with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
                    cursor = connection.cursor()
                    sql = "REPLACE INTO plants (plant,Kc,dry,sun) VALUES(?,?,?,?)"
                    cursor.execute(sql,plants[index])
                    connection.commit()
        #if plant parameters changes are canceled
        if "cancel" in request.form:
            pass
        
        #if new line of plant parameters
        if "addline" in request.form:
            param = []
            if str(request.form["plant"]) != "" and str(request.form["Kc"]) != "" and str(request.form["threshold"]) != "" and str(request.form["sun"]) != "" :
                print(str(request.form["plant"]))
                param.append(str(request.form["plant"]))
                print(str(float(request.form["Kc"])))
                param.append(float(request.form["Kc"]))
                print(str(float(request.form["threshold"])))
                param.append(float(request.form["threshold"]))
                print(str(request.form["sun"]))
                param.append(str(request.form["sun"]))
                with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
                    cursor = connection.cursor()
                    sql = "INSERT INTO plants (plant,Kc,dry,sun) VALUES(?,?,?,?)"
                    cursor.execute(sql,param)
                    connection.commit()

        #if request for plant parameters edition or removal
        for plant in plants:
            if "edit"+plant[0] in request.form:
                edit = plant[0]
            if "remove"+plant[0] in request.form:
                with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
                    cursor = connection.cursor()
                    sql = "DELETE FROM plants WHERE plant = '" + str(plant[0]) + "'"
                    cursor.execute(sql)
                    connection.commit()

        with sqlite3.connect(PLANTS_LOGIN, timeout=10) as connection:
            cursor = connection.cursor()
            sql = "SELECT plant, Kc, dry, sun FROM plants ORDER BY plant ASC"
            cursor.execute(sql)
            plants = cursor.fetchall()
        plants = [[str(param[j]) for j in range(len(plants[0]))] for param in plants]

        return render_template("database.html",plants = plants,edit=edit)


@app.route("/restart", methods = ['GET'])
def restart():
    if request.method == 'GET':
        os.system('sudo reboot now')


if __name__ == '__main__':
    try:
        i2cInstance.scan()
        for device in i2cInstance.devices:
            i2cInstance.Off(device)
        try:
            if sys.argv[1] == 'y':
                with sqlite3.connect(PLANTS_LOGIN,timeout=10) as connection:
                    cursor = connection.cursor()
                    sql_drop = "DROP TABLE IF EXISTS plants"
                    cursor.execute(sql_drop)
                    cursor.execute(PLANTS_CONFIG)
                    cursor.execute(FILL_PLANTS)
                    connection.commit()
                with sqlite3.connect(MEASUREMENTS_LOGIN,timeout=10) as connection:
                    measureCursor = connection.cursor()
                    for device in i2cInstance.available_adresses:
                        sql_drop = "DROP TABLE IF EXISTS hygrometry"+str(device)
                        measureCursor.execute(sql_drop)
                        sql = HYGROMETRY_TABLE.format("hygrometry"+str(device))
                        measureCursor.execute(sql)
                        connection.commit()
#                    for device in i2cInstance.devices:
#                        sql_drop = "DROP TABLE IF EXISTS hygrometry"+str(device)
#                        measureCursor.execute(sql_drop)
#                        sql = HYGROMETRY_TABLE.format("hygrometry"+str(device))
#                        measureCursor.execute(sql)
                with sqlite3.connect(CONTROLS_LOGIN,timeout=10) as connection:
                    controlsCursor = connection.cursor()
                    sql_drop = "DROP TABLE IF EXISTS controls"
                    controlsCursor.execute(sql_drop)
                    controlsCursor.execute(CONTROLS_TABLE)
                    controlsCursor.execute(FILL_CONTROLS)

                    sql_hours_drop = "DROP TABLE IF EXISTS hours"
                    controlsCursor.execute(sql_hours_drop)
                    controlsCursor.execute(HOURS_TABLE)
                    connection.commit()
        except:
            pass
        thr = Thread(target = poll_data, args=(i2cInstance,pi))
        thr.daemon = True
        thr.start()
        thr2 = Thread(target = automatic, args=(i2cInstance,pi,motor))
        thr2.daemon = True
        thr2.start()
        http_server.serve_forever() 
        #app.run(**FLASK_CONFIG)

    except(KeyboardInterrupt):
        raise
    finally:
        if len(i2cInstance.watering) >0:
            i2cInstance.Off(i2cInstance.watering[0])
        with sqlite3.connect(CONTROLS_LOGIN) as connection:
            cursor = connection.cursor()
            cursor.execute(UPDATE_CONTROLS,["watering",0])
            connection.commit()


