# Modular watering system for domotic

System based on Flask with some javascript to automate irrigation for interior plants

## Install

This project is due to be used on a raspberry pi or equivalent
You can start off by cloning the repo and install the requirements (in the requirements.txt file)

the system can be configured with a NAS. Here is an example ith a synology NAS to mount the drive
```bash
sudo mount -t cifs -o user=usr,domain=.,password=psswd,vers=1.0 //NAS_IP/Moduwat /media/NAS/
```

Before launching anything, make sure pigpiod is started with
```bash
sudo pigpiod
```

## launch
When first launching the app use the below command to crate the database files
```bash
python moduwat.py
```
When you wish to restart the project use the following command instead
```bash
python moduwat.py
```
mount to NAS
```bash
sudo mount -t cifs -o user=usr,domain=.,password=psswd,vers=1.0 //NAS_IP/Moduwat /media/NAS/
```

## Links
This project is linked to its mechanical parts and to its microcontroller parts:
https://cad.onshape.com/documents/2c8491ba2fe2ede58bab1cbd/w/e99b41dd62d65d067991ba2a/e/5d2006eac134f4ebddaeb74f
https://github.com/Ryuk4/attiny-modular-slave

## Contributing
This is an open source project and you can contribute by posting issues. I'm fully open to upgrades to the project


## ToDoList
OK graph title as plant name instead of sensor number
watering activation needs to be recorded: OK
    -change database structure of plants OK
    -add recording in the poll data thread OK
    -add watering activation in json data as /activation+sensor_id OK
    -add watering activation in graph data displayed OK
    
correction to be made for speed reading when automatic watering (not activated RN)

activation threshold needs to be recorded: OK
    -change database structure of plants OK
    -add recording in the poll data thread OK
    -add watering threshold in json data as /threshold+sensor_id OK
    -add watering threshold in graph data displayed as plotband OK

log file needs to be implemented

timeslots for the week need to be implemented:
    -change table structure OK
    -change database structure of timeslots OK
    -change handling of time : show week recap with weeks list and savetheweek button and days as buttons
    - show days with start stop to be edited as is now
    - open daily_timeslot with day argument
    -add detection of day of the week
    
different weekly timeslots need to be implemented (vacation, workweek etc...):
    -add list to be chosen from with new database structure (TBD)
water level in the tank needs to be recorded with alarm in case of low level
total flow or individual flow for each plant is faulty. Needs to be corrected
flows for each plant need to be recorded:
    -change database structure of plants OK
    -add recording in TBD thread
    




## License
[MIT](https://choosealicense.com/licenses/mit/)




