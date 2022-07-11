import machine
led = machine.Pin('LED', machine.Pin.OUT)
sw = machine.Pin(19,machine.Pin.IN,machine.Pin.PULL_UP)

#on test to prevent to always blank flashing the pico
#I used GPIO(19) to detect if I want to break the system instead of running the MQTT script
if  sw.value():
    import mqtt_ds18B20.py
else:
    led.value(0)
    sys.exit()
