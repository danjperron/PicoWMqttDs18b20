import machine
led = machine.Pin('LED', machine.Pin.OUT)
sw = machine.Pin(19,machine.Pin.IN,machine.Pin.PULL_UP)

if  sw.value():
    import mqt4
else:
    led.value(0)
    sys.exit()
