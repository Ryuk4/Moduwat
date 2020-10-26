# -*- coding: utf-8 -*-

CONTROLS_LOGIN = "/media/NAS/controls.db"
MEASUREMENTS_LOGIN = "/media/NAS/measurements.db"

CONTROLS_TABLE = '''
CREATE TABLE IF NOT EXISTS controls (
    variable VARCHAR UNIQUE,
    data INT
)
'''
FILL_CONTROLS = '''
INSERT INTO controls
	(variable,data)
VALUES
	("next",0),
	("watering",0);
'''

HYGROMETRY_TABLE = '''
CREATE TABLE IF NOT EXISTS {} (
    time INT UNIQUE,
    measure INT
)
'''

PLANTS_CONFIG = {
    'Basil'     : {'Kc' : 0.8 ,'soil' : 0.6 , 'sun' : 'direct'},
    'Chive'     : {'Kc' : 0.8 ,'soil' : 0.6 , 'sun' : 'mi ombre'},
    'Cilantro'  : {'Kc' : 0.8 ,'soil' : 0.6 , 'sun' : 'direct'},
    'Dill'      : {'Kc' : 0.8 ,'soil' : 0.4 , 'sun' : 'direct'},
    'Lemongrass': {'Kc' : 1.2 ,'soil' : 0.6 , 'sun' : 'direct'},
    'Mint'      : {'Kc' : 0.8 ,'soil' : 0.8 , 'sun' : 'mi ombre'},
    'Parsley'   : {'Kc' : 0.8 ,'soil' : 0.6 , 'sun' : 'mi ombre'},
    'Pepper'    : {'Kc' : 0.8 ,'soil' : 0.6 , 'sun' : 'direct'},
    'Rosemary'  : {'Kc' : 0.4 ,'soil' : 0.4 , 'sun' : 'direct'},
    'Sage'      : {'Kc' : 0.4 ,'soil' : 0.4 , 'sun' : 'direct'},
    'Tarragon'  : {'Kc' : 0.8 ,'soil' : 0.6 , 'sun' : 'direct'}
}


ETP_CONFIG = [
    1, #january
    2, #February
    3, #March
    4, #April
    5, #May
    6, #June
    7, #July
    6, #August
    5, #September
    4, #October
    3, #November
    2  #December
]



UPDATE_CONTROLS = '''REPLACE INTO controls(variable,data) VALUES(?,?)'''

INSERT_HYGRO = '''INSERT INTO {} (time,measure) VALUES (?,?)'''

FLASK_CONFIG = {
    'host'      : '0.0.0.0', # allows connection outside of localhost
    'port'      : 9090,
    'debug'     : True ,
    'threaded'  : True,
}
