Modular watering system for domotic

System based on Flask with some javascript to automate irrigation in the garden


launch
sudo python moduwat.py

mount to NAS
sudo mount -t cifs -o user=usr,domain=.,password=psswd,vers=1.0 //NAS_IP/Moduwat /media/NAS/


requirements
sqlite3
flask
pigpiod






"CREATE TABLE controls (variable VARCHAR, data INT)"
+-----------+------------+
| variable  | data       |
+-----------+------------+
| mode      |          0 |
| next      | 1591295229 |
| threshold |         10 |
| watering  |          0 |
+-----------+------------+


+------------+---------+
| time       | measure |
+------------+---------+
| 1589541539 |     100 |
| 1589541541 |     100 |

