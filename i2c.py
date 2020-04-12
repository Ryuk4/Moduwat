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
			print(str(device)+' '+str(time.time()))
			h=self.pi.i2c_open(1,device)
			try:
				self.pi.i2c_write_byte(h,0x00)
				time.sleep(0.5)
			except:
				if device in self.devices:
					del self.devices[self.devices.index(device)]
					self.available_adresses.append(device)
					self.available_adresses.sort()
				self.pi.i2c_close(h)
				continue

			if device == 3:
				self.change_adress(device,self.available_adresses[0])
				time.sleep(0.5)
				self.pi.i2c_close(h)

			elif device in self.devices:
				self.pi.i2c_close(h)
			else:
				self.devices.append(device)
				self.devices.sort()
				del self.available_adresses[self.available_adresses.index(device)]
				self.pi.i2c_close(h)
		print self.available_adresses

	def change_adress(self, old_adr, new_adr):
		h=self.pi.i2c_open(1,old_adr)
		self.pi.i2c_write_byte(h, 0xC1)
		time.sleep(0.5)
		self.pi.i2c_write_byte(h, new_adr)
		time.sleep(0.5)
		self.pi.i2c_close(h)
		if new_adr != 3:
			del self.available_adresses[self.available_adresses.index(new_adr)]
		if old_adr != 3:
			del self.devices[self.devices.index(old_adr)]
			self.available_adresses.append(old_adr)
			self.available_adresses.sort()
		self.devices.append(new_adr)
		self.devices.sort()

	def write(self, device, pwm) :
		if pwm <= 255 and pwm >= 0:
			h = self.pi.i2c_open(1 , device)
			self.pi.i2c_write_byte(h, 0xC2)
			time.sleep(0.5)
			self.pi.i2c_write_byte(h, pwm)
			self.pi.i2c_close(h)
		else:
			pass

	def On(self, device) :
		h=self.pi.i2c_open(1,device)
		self.pi.i2c_write_byte(h,0x02)
		self.pi.i2c_close(h)

        def Off(self, device) :
                h=self.pi.i2c_open(1,device)
                self.pi.i2c_write_byte(h,0x01)
                self.pi.i2c_close(h)


	def read_sensor(self, device):
		h=self.pi.i2c_open(1,device)
		try:
			val = int(self.pi.i2c_read_byte(h))
			val = 100-val*100/255
			self.pi.i2c_close(h)
			return val
		except e:
			print e

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
