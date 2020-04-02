#!/usr/bin/env python
import pigpio, time, os
import datetime
import pytz
from sys import stdout



class I2c(object):
	def __init__(self,pi):
		self.available_adresses = range(4,70)
		self.handles = []
		self.devices = []
		self.dataList = []
		self.pi=pi
	def scan(self):
		for device in range(3,70):
			h=self.pi.i2c_open(1,device)
			try:
				self.pi.i2c_write_byte(h,0x01)
				time.sleep(0.5)
			except:
				if device in self.devices:
					del self.devices[self.devices.index(device)]
					self.available_adresses.append(device)
				self.pi.i2c_close(h)
				continue

			if device == 3:
				self.change_adress(device,self.available_adresses[0])
				time.sleep(0.5)
				self.devices.append(self.available_adresses[0])
				del self.available_adresses[0]
				self.pi.i2c_close(h)
			elif device in self.devices:
				self.pi.i2c_close(h)
			else:
				self.devices.append(device)
				self.pi.i2c_close(h)

	def change_adress(self, handleNumber, new_addr):
		h=self.pi.i2c_open(1,handleNumber)
		self.pi.i2c_write_byte(h, 0xC1)
		time.sleep(0.5)
		self.pi.i2c_write_byte(h, new_addr)
		time.sleep(0.5)
		self.pi.i2c_close(h)


	def write(self, handleNumber, pwm) :
		if pwm <= 255 and pwm >= 0:
			self.pi.i2c_write_byte(self.handles[handleNumber], 0xC2)
			time.sleep(0.5)
			self.pi.i2c_write_byte(self.handles[handleNumber], pwm)
		else:
			pass

	def read_sensor(self, handleNumber):
		"""pi.i2c_write_byte(self.handles[handleNumber], 0x10)
		time.sleep(0.5)"""
		h=self.pi.i2c_open(1,handleNumber)
		val = int(self.pi.i2c_read_byte(h)) #(self.handles[handleNumber])
		val = val*100/255
		self.pi.i2c_close(h)
		#print val
		return val

	def to_unix_timestamp(self,ts):
		"""
		Get the unix timestamp (seconds from Unix epoch) 
		from a datetime object
		"""
		start = datetime.datetime(year=1970, month=1, day=1)
		diff = ts - start
		return diff.total_seconds()

	def read_sensors(self):
		n = datetime.datetime.now()
		timestamp = self.to_unix_timestamp(n)
		self.dataList[0].append(timestamp)
		for handle in range(len(self.handles)):
			try:
				self.dataList[handle+1].append(read_sensor)
			except:
				self.dataList[handle+1].append(None)
