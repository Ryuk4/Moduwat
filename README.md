Modular watering system for domotic

System based on Flask with some javascript to automate irrigation in the garden


launch
python moduwat.py or python moduwat.py y (if you want to reset databases or create them)

mount to NAS
sudo mount -t cifs -o user=usr,domain=.,password=psswd,vers=1.0 //NAS_IP/Moduwat /media/NAS/


requirements
sqlite3
flask
pigpiod


ToDoList
reset database
authorized hours that are editable







