# -*- coding: utf-8 -*-

CONTROLS_LOGIN = "/media/NAS/controls.db"
MEASUREMENTS_LOGIN = "/media/NAS/measurements.db"

CONTROLS_TABLE = '''
CREATE TABLE IF NOT EXISTS controls (
    variable VARCHAR UNIQUE,
    data INT
)
'''

HYGROMETRY_TABLE = '''
CREATE TABLE IF NOT EXISTS {} (
    time INT UNIQUE,
    measure INT
)
'''

UPDATE_CONTROLS = '''REPLACE INTO controls(variable,data) VALUES(?,?)'''

INSERT_HYGRO = '''INSERT INTO {} (time,measure) VALUES (?,?)'''

FLASK_CONFIG = {
    'host'      : '0.0.0.0', # allows connection outside of localhost
    'port'      : 9090,
    'debug'     : False ,
    'threaded'  : True,
}
