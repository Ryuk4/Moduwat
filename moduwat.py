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
        now = time.time()
        next=now+5
        first = time.time()
        while True:
                time.sleep(0.5)
                #print time.time()-now
                #if time.time()>next:
                #       next=time.time()+5
                #       print next


                #time.sleep(0.5)
                #if time.time()>next:
                #if piCall.read(23) == 1:
                        #print i2cCall.dataList
                if time.time()>next:
                        #print "pass1"
                        next=time.time()+360
                        #if piCall.read(23) ==1:
                                #print "pass"
                                #print next-time.time()
                                #next=time.time()+5
                                #print next-time.time()
			piCall.write(18,1)
			time.sleep(5)
                        read = i2cCall.read_sensor(i2cCall.devices[0])


                        #try:
                        #        read=int(i2cCall.dataList[1][-1])
                                        #read=read/100.0
                        #except:
                        #        read=None
 #                       print "read"+str(read)
                        now = time.time()
                        now2=time.time()-first
                        #now2=int(now2*1000)
                        sql = "INSERT INTO hygrometry1 (time,measure) VALUES (%s,%s)"
                        if read is not None:
                                values.append((now,read))
                                now3=int(now)
                                read2=int(read)
                                #print type(now3), type(read2)
                                val = (now3,read2)
                                #print val
                                sqlCursor.execute(sql,val)
                                mydb.commit()
                        #print values
#                        print next-now
                        time.sleep(1)
			piCall.write(18,0)
                #elif piCall.read(23) == 0:
                        #print 1
                        #i2cCall.scan()
                        #time.sleep(10)



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
        #print results
        return json.dumps(results)

@app.route("/graph")
def graph():
        return render_template("graph.html")

#@app.route("/settings")
#def index():
#	return render_template("settings.html")

@app.route("/settings", methods = ['POST'])
def settings():
	message=''
	bar=[]
	if request.method == 'POST' :
		if 'submit' in request.form:
			f_adress = int(request.form["faddress"])
			n_adress = int(request.form["naddress"])
#			i2cInstance.write(f_adress,0xC1)
#			i2cInstance.write(f_adress,n_adress)
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

                thr = Thread(target = poll_data, args=(i2cInstance,pi,mycursor))
                thr.daemon = True
                thr.start()

                app.run(host='0.0.0.0', debug=True ,port=9090)

        except(KeyboardInterrupt):
                mydb.close()
                raise


