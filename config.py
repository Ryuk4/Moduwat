# -*- coding: utf-8 -*-

CONTROLS_LOGIN = "/media/NAS/controls.db"
MEASUREMENTS_LOGIN = "/media/NAS/measurements.db"
PLANTS_LOGIN = "/media/NAS/plants.db"

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

PLANTS_CONFIG = '''
CREATE TABLE IF NOT EXISTS plants (
    plant VARCHAR UNIQUE,
    Kc float,
    dry float,
    sun VARCHAR
)
'''

FILL_PLANTS = '''
INSERT INTO plants
	(plant,Kc,dry,sun)
VALUES
	('Avocado'   , 1.0 , 0.7 , 'direct'),
	('Basil'     , 0.8 , 0.6 , 'direct'),
	('Chive'     , 0.8 , 0.6 , 'mi ombre'),
	('Cilantro'  , 0.8 , 0.6 , 'direct'),
	('Dill'      , 0.8 , 0.4 , 'direct'),
	('Lemongrass', 1.2 , 0.6 , 'direct'),
	('Mint'      , 0.8 , 0.8 , 'mi ombre'),
   ('Mushroom'  , 0.4 , 0.9 , 'ombre'),
	('Parsley'   , 0.8 , 0.6 , 'mi ombre'),
	('Pepper'    , 0.8 , 0.6 , 'direct'),
	('Rosemary'  , 0.4 , 0.4 , 'direct'),
	('Sage'      , 0.4 , 0.4 , 'direct'),
	('Tarragon'  , 0.8 , 0.6 , 'direct');
'''

HOURS_TABLE = '''
CREATE TABLE IF NOT EXISTS hours (
    time start,
    time stop
)
'''

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
