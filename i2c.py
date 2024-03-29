#!/usr/bin/env python
import time
import datetime



class I2c(object):
    def __init__(self,pi):
        self.available_adresses = list(range(4,70))
        self.handles = []
        self.devices = []
        self.watering = []
        self.dataList = []
        self.threshold = {}
        self.flow = {}
        self.pi = pi
        self.dry_list = []
        self.plant_type = {}
        self.mode = {}
    def scan(self):
        for device in range(3,70):
            #print(str(device)+' '+str(time.time()))
            h=self.pi.i2c_open(1,device)
            try:
                self.pi.i2c_write_byte(h,0x00)
                time.sleep(0.5)
            except:
                if device in self.devices:
                    try:
                        self.pi.i2c_write_byte(h,0x00)
                        time.sleep(0.5)
                    except:
                        del self.devices[self.devices.index(device)]
                        self.available_adresses.append(device)
                        self.available_adresses.sort()
                        del self.threshold[str(device)]
                        del self.flow[str(device)]
                        del self.mode[str(device)]
                self.pi.i2c_close(h)
                continue

            if device == 3:
                self.Off(device)
                self.change_adress(device,self.available_adresses[0])
                time.sleep(0.5)
                self.pi.i2c_close(h)

            elif device in self.devices:
                self.pi.i2c_close(h)
            else:
                self.devices.append(device)
                self.threshold[str(device)] = 10
                self.plant_type[str(device)] = "Select"
                self.mode[str(device)] = "Manual"
                self.flow[str(device)] = 0
                self.devices.sort()
                del self.available_adresses[self.available_adresses.index(device)]
                self.pi.i2c_close(h)
        #print self.available_adresses

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
            self.flow[str(new_adr)] = self.flow[str(old_adr)]
            del self.flow[str(old_adr)]
            self.threshold[str(new_adr)] = self.threshold[str(old_adr)]
            del self.threshold[str(old_adr)]
            self.mode[str(new_adr)] = self.mode[str(old_adr)]
            del self.mode[str(old_adr)]
            self.plant_type[str(new_adr)] = self.plant_type[str(old_adr)]
            del self.plant_type[str(old_adr)]


        elif old_adr == 3:
            self.flow[str(new_adr)] = 0
            self.threshold[str(new_adr)] = 10
            self.mode[str(new_adr)] = "Manual"
            self.plant_type[str(new_adr)] = "Select"
        if old_adr in self.watering:
            del self.watering[self.watering.index(old_adr)]
            self.watering.append(new_adr)
        self.devices.append(new_adr)
        #self.mode[str(new_adr)]= "Manual"
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
        try:
            h=self.pi.i2c_open(1,device)
            self.pi.i2c_write_byte(h,0x02)
            self.pi.i2c_close(h)
        except:
            self.pi.i2c_close(h)
            self.On(device)
        if device not in self.watering:
            self.watering.append(device)

    def Off(self, device) :
        try:
            h = self.pi.i2c_open(1,device)
            self.pi.i2c_write_byte(h,0x01)
            self.pi.i2c_close(h)
        except:
            self.pi.i2c_close(h)
            self.Off(device)
        if device in self.watering:
            del self.watering[self.watering.index(device)]

    def read_sensor(self, device):
        h=self.pi.i2c_open(1,device)
        try:
            val = float(self.pi.i2c_read_byte(h))
            print("sensor value "+ str(val))
            val = val/255.0*3.3
            #print val
            #val = (((1.0/val)*2.48)-0.72)*100.0
            #print val
            val = ((564.3/(val+2.97)-90)-7)*100/34
            val = int(val)
            if val>100:
                val=100
            #val = 100-(val-100)/1.2
            print("humidity "+str(val)+"%")
            self.pi.i2c_close(h)
            return val
        except Exception as e:
            self.pi.i2c_close(h)
            print(e)

    def to_unix_timestamp(self,ts):
        """Get the unix timestamp (seconds from Unix epoch) 
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
                self.dataList[handle+1].append(self.read_sensor())
            except:
                self.dataList[handle+1].append(None)
