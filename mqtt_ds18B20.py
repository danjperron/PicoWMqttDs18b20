import machine
import rp2
import network
import ubinascii
import time
import sys
from secrets import secrets
from onewire import OneWire
from ds18x20 import DS18X20
from umqtt.simple import MQTTClient
from machine import Pin

#led declaration
led = machine.Pin('LED', machine.Pin.OUT)


#DS18B20 declaration. Use specific sensor ID to reduce time (no scan needed).
sensor = (0x28,0xff,0x69,0x67,0xc1,0x17,0x01,0x98)
#sensor DS18b20 on pin 28
ds = DS18X20(OneWire(machine.Pin(28)))


#cpu temperature declaration
cpu_temp = machine.ADC(machine.ADC.CORE_TEMP)
conversion_factor = 3.3 / (65535)

def readCpuTemperature():
  reading = cpu_temp.read_u16() * conversion_factor
  return 27 - (reading - 0.706)/0.001721
    
#Vsys Voltage
#N.B. Can't use ADC(29). it crashes!!!!
#to get around it we need to declare ADC(3),
# getPads, setPads, readADC and then put back the original Pads
#set or get GPIO pads settings. Need on Pin29

def setPad(gpio, value):
    machine.mem32[0x4001c000 | (4+ (4 * gpio))] = value
    
def getPad(gpio):
    return machine.mem32[0x4001c000 | (4+ (4 * gpio))]

def readVsys():
    oldpad = getPad(29)
    setPad(29,128)  #no pulls, no output, no input
    adc_Vsys = machine.ADC(3)
    Vsys = adc_Vsys.read_u16() * 3.0 * conversion_factor
    setPad(29,oldpad)
    return Vsys
    

#network declaration
# Set country to avoid possible errors / https://randomnerdtutorials.com/micropython-mqtt-esp32-esp8266/
rp2.country('CA')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# See the MAC address in the wireless chip OTP
#mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
#print('mac = ' + mac)


# Load login data from different file for safety reasons

#set static IP
# (IP,mask,gateway,dns)
wlan.ifconfig(('10.11.12.21', '255.255.255.0', '10.11.12.253', '8.8.8.8'))

#connect using ssid
wlan.connect(secrets['ssid'],secrets['pw'])
while not wlan.isconnected():
    machine.idle() # save power while waiting

# Wait for connection with 10 second timeout
timeout = 10
while timeout > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    timeout -= 1
    print('Waiting for connection...')
    time.sleep(1)
    
# Handle connection error
# Error meanings
# 0  Link Down
# 1  Link Join
# 2  Link NoIp
# 3  Link Up
# -1 Link Fail
# -2 Link NoNet
# -3 Link BadAuth

if wlan.status() != 3:
    raise RuntimeError('Wi-Fi connection failed')
else:
    for i in range(wlan.status()):
        led.on()
        time.sleep(.1)
        led.off()
    print('Connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])
    
###MQTT  Topic Setup ###

def connectMQTT():
  client = MQTTClient(secrets['client_id'],secrets['broker'])
  client.connect()
  return client


def publish(topic, value):
  print(topic)
  print(value)
  pub_msg = "%5.2f" % value
  print(topic,"  ",pub_msg)
  client.publish(topic, pub_msg)
  print("publish Done")


try:
  client = connectMQTT()
except OSError as e:
  machine.reset()





def getSensorsAndPublish():
  # start DS18B20 conversion
  ds.convert_temp()
  # record time in nanosecond
  startConv_ms = time.ticks_ms()
  # end need to be 750ms after
  endConv_ms = startConv_ms + 750
  # read cpu Temperature
  publish(secrets['pubtopicTempCPU'],readCpuTemperature())
  # read Vsys
  publish(secrets['pubtopicVsys'], readVsys())
  # DS18b20 needs 750ms after conversion
  while time.ticks_ms() < endConv_ms:
      pass
  publish(secrets['pubtopicTemp'], ds.read_temp(sensor))
  
 
#ok main process
  
#Using lightsleep?
  
UsingLightSleep = True
 

try:  
    while True:
        led.value(True) 
        getSensorsAndPublish()
        led.value(False)
        time.sleep(1)
        if UsingLightSleep:
            client.disconnect()
            wlan.disconnect()
            wlan.active(False)
            wlan.deinit()
            time.sleep_ms(500)
            machine.lightsleep(120000)
            break
        else:
            time.sleep(10)
except OSError as e:
  pass
machine.reset()
