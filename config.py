# -*- coding: utf-8 -*-

CONTROLS_LOGIN = "/media/NAS/controls.db"
MEASUREMENTS_LOGIN = "/media/NAS/measurements.db"

CONTROLS_TABLE = '''
CREATE TABLE IF NOT EXISTS watered_schedule (
    date_watered TIMESTAMP,
    PRIMARY KEY(date_watered)
)
'''

SCHEDULE_TABLE = '''
CREATE TABLE IF NOT EXISTS schedule (
    date TIMESTAMP,
    voltage FLOAT,
    temp FLOAT,
    humidity FLOAT,
    PRIMARY KEY(date)
)
'''

FLASK_CONFIG = {
    'host'  : '0.0.0.0', # allows connection outside of localhost
    'port'  : 5000,
    'debug' : True ,
}
