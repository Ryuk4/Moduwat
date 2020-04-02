#!/usr/bin/env python
from flask import Flask, render_template, Response, jsonify, request
from jinja2 import Template
import json
import pigpio
from i2c import I2c
import time
from threading import Thread
import codecs
from collections import deque
import pymysql
import pymysql.cursors
import sys

values = deque(maxlen=1000)


WATER = "water"

AVAILABLE_COMMANDS = {
	'Water' : WATER
}

pi=pigpio.pi()
pi.set_mode(23,pigpio.INPUT)
pi.set_pull_up_down(23,pigpio.PUD_UP)
i2cInstance = I2c(pi)



app= Flask(__name__)


def poll_data(i2cCall,piCall,sqlCursor):
        next=time.time()
        while True:
                if time.time()>next:
                        next=time.time()+10
                        read = i2cCall.read_sensor(i2cCall.devices[0])
                        now = time.time()

                        sql = "INSERT INTO hygrometry1 (time,measure) VALUES (%s,%s)"
                        if read is not None:
                                values.append((now,read))
                                val = (now,read)
                                sqlCursor.execute(sql,val)
                                mydb.commit()


@app.route("/data.json")
def data():
        mydb = pymysql.connect(
                host = "localhost",
                user = str(sys.argv[1]),
                passwd = str(sys.argv[2]),
                db = "measurements"
        )
        cursor=mydb.cursor()
        cursor.execute("SELECT 1000*time, measure from hygrometry1")
        results = cursor.fetchall()
        return json.dumps(results)

@app.route("/graph")
def graph():
        return render_template("graph.html")

@app.route("/settings")
def index():
	return render_template("settings.html")

@app.route("/settings", methods = ['POST'])
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

@app.route("/<cmd>")
def command(cmd=None):
	command=cmd.upper()
	if command == 'WATER':
		pass
		#i2cInstance.write(0x4,0xC2)
		#i2cInstance.write(0x4,255)


if __name__ == '__main__':
        try:
#                pi=pigpio.pi()
#                pi.set_mode(23,pigpio.INPUT)
#                pi.set_pull_up_down(23,pigpio.PUD_UP)
#                i2cInstance = I2c(pi)
                mydb = pymysql.connect(
                        host = 'localhost',
                        user = str(sys.argv[1]),
                        passwd = str(sys.argv[2]),
			database = 'measurements'
                )
                mycursor = mydb.cursor()
		i2cInstance.scan()
                thr = Thread(target = poll_data, args=(i2cInstance,pi,mycursor))
                thr.daemon = True
                thr.start()

                app.run(host='0.0.0.0', debug=True ,port=9090)

        except(KeyboardInterrupt):
                mydb.close()
                raise


