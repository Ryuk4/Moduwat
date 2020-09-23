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
	("mode",0),
	("next",0),
	("threshold",10),
	("watering",0);
'''

HYGROMETRY_TABLE = '''
CREATE TABLE IF NOT EXISTS {} (
    time INT UNIQUE,
    measure INT
)
'''

#Rosemary besoin en eau faible, sol sec entre arrosages, soleil direct
#Basil besoin en eau moyen, sol drainé entre arrosages, soleil direct
#Dill (aneth) besoin en eau moyen, sol sec entre arrosages, soleil 
#Cilantro (coriandre) besoin en eau moyen, sol drainé entre arrosage, soleil
#Tarragon (Estragon) besoin en eau moyen, sol drainé entre arrosage, soleil
#Parsley besoin en eau moyen, sol drainé, mi ombre
#Chive (Ciboulette) besoin en eau moyen, sol drainé, mi ombre
#Sage (sauge) besoin en eau faible, sol sec entre arrosages, soleil direct





UPDATE_CONTROLS = '''REPLACE INTO controls(variable,data) VALUES(?,?)'''

INSERT_HYGRO = '''INSERT INTO {} (time,measure) VALUES (?,?)'''

FLASK_CONFIG = {
    'host'      : '0.0.0.0', # allows connection outside of localhost
    'port'      : 9090,
    'debug'     : False ,
    'threaded'  : True,
}
