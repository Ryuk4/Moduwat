#!/usr/bin/env python
# -*- coding: utf-8 -*-

import  time
import pigpio


class Motor(object):
        def __init__(self,pi):
		self.speed = 0
		self.direction = 1
		self.flowr = 0
		self.flowrate = 0.448 #basic flowrate in mL/min for speed = 1000 tr/min
		self.start_water = 0
		self.watering = False
		self.DIR = 23 #direction pin
		self.STEP = 18 #step pin (the one that makes the motor turn
		self.enable = 24 #enable is 1 to stop the drv8825 and 0 to enable it
		self.SPR = 48 #48 steps per turn of the motor
                self.pi=pi
		self.pi.set_mode(self.DIR, pigpio.OUTPUT)
		self.pi.set_mode(self.STEP,pigpio.OUTPUT)
		self.pi.set_mode(self.enable, pigpio.OUTPUT)
		self.pi.write(self.enable, 1)
		self.pi.write(self.DIR, 1)
		self.ramp_time = 0
		self.previous_spd = 0
		self.previous_dir = 0

        def turn(self,speed,direction,ramp_time):
		"""things that still need to be coded :
		- how to ramp if new speed is in opposite direction (idea to use time.sleep for the time the motor ramps down then change pin direction and then send wave chain with new ramping up)
		"""
		self.pi.write(self.enable, 0)
		#self.flow()
		self.previous_spd = self.speed
		#10 intermediate speeds
		self.previous_dir = self.direction

		diff_speed = direction*speed-self.previous_dir*self.previous_spd
		speeds = []
		ramp = []
		for i in range(10):
			speeds.append(self.previous_dir*self.previous_spd+diff_speed/10*(i+1))
			ramp.append([speeds[i],int(ramp_time/10.0*abs(speeds[i])/60*48)])
		#ramp[9][1] = 10000
		#print(ramp)
		self.pi.wave_clear()
		wid = [-1]*10
		for i in range(10):
			frequency = ramp[i][0]
			if frequency == 0:
				pass
			else :
				micros = int(500000 / frequency)
				wf = []
				wf.append(pigpio.pulse(1 << self.STEP, 0, micros))  # pulse on
				wf.append(pigpio.pulse(0, 1 << self.STEP, micros))  # pulse off
				self.pi.wave_add_generic(wf)
				wid[i] = self.pi.wave_create()

		chain = []
		for i in range(9):
			steps = ramp[i][1]
			x = steps & 255
			y = steps >> 8
			chain += [255, 0, wid[i], 255, 1, x, y]
		if ramp[9][0] == 0:
			pass
		else :
			chain += [255, 0, wid[9], 255, 3]
		self.pi.wave_chain(chain)  # Transmit chain.
		self.ramp_time = ramp_time
		self.speed = speed
		self.direction = direction
		self.start_water = time.time()
		self.watering = True
		time.sleep(ramp_time)
		flow = self.flow()
		#print self.speed
		return flow


	def off(self,ramp_time):
		flow = self.turn(0,1,ramp_time)
		self.pi.write(self.enable,1)
		self.watering = False
		return flow

	def flow(self):
		new_flow = 0
		if self.watering : #if watering then flow can be updated
			now = time.time()
			water_time = now - self.start_water #time from when it started watering or when flow was last used
			#flow calculations positive if direction is 1 and negative if position is 0
			if self.direction == 0:
				direction = -1
			else :
				direction = 1

			if water_time > self.ramp_time : #if ramping to speed is finished then flow = ramp flow + flow till end of ramping
				ramp_flow =  ((direction*self.speed-self.previous_dir*self.previous_spd)/2 + self.previous_dir*self.previous_spd) * self.ramp_time * self.flowrate /1000/60
				new_flow += ramp_flow
				new_flow += direction * self.speed * (water_time - self.ramp_time) * self.flowrate /1000/60

			else : #else flow = ramp flow
				ramp_flow =  ((direction*self.speed-self.previous_dir*self.previous_spd)/2 + self.previous_dir*self.previous_spd) * water_time * self.flowrate /1000/60
				new_flow += ramp_flow
			self.flowr += new_flow
			#print new_flow
			#let s prevent calculation of another ramping if speed hasn't changed
			self.previous_spd = self.speed
			self.previous_dir = self.direction
			self.start_water = time.time()
			return new_flow

		else : #else same flow as before
			return new_flow

