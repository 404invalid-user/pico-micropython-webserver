import network as net
import uasyncio as a
import json
from random import randint
from machine import Pin
import gc

from lib import PicoWebServer



# get config
def LoadConfig(file):
    f = open(file)
    text = f.read()
    f.close()
    return json.loads(text)
config = LoadConfig('config.json')

# this lock will be used for data interchange between loops
# better choice is to use uasynio.queue, but it is not documented yet
lock = a.Lock()


# SSID - network name
# pwd - password
# attempts - how many time will we try to connect to WiFi in one cycle
# delay_in_msec - delay duration between attempts
async def wifi_connect(hostname: str, SSID: str, pwd: str, attempts: int = 3, delay_in_msec: int = 200) -> network.WLAN:
    wifi = net.WLAN(net.STA_IF)
    wifi.active(True)
    #not working no clue why
    #wifi.config(dhcp_hostname = "PI-Pico")
    count = 1
    while not wifi.isconnected() and count <= attempts:
        print("WiFi connecting. Attempt {}.".format(count))
        if wifi.status() != net.STAT_CONNECTING:
            wifi.connect(SSID, pwd)
        await a.sleep_ms(delay_in_msec)
        count += 1
    if wifi.isconnected():
        print("ifconfig: {}".format(wifi.ifconfig()))
    else:
        print("Wifi not connected.")
    return wifi

# Task for read loop
async def run():
    global config
    global lock

    wifi = await wifi_connect("PI-Pico", config["wifi"]["SSID"], config["wifi"]["password"])
    #retyrn wifi if not connected
    while True:
        gc.collect()
        if not wifi.isconnected():
            wifi = await wifi_connect("PI-Pico", config["wifi"]["SSID"], config["wifi"]["password"])
            if not wifi.isconnected():
                continue
        
        webserver = PicoWebServer.WebServer()
        
        def getIndex(req,res):
            f = open('html/index.html')
            text = f.read()
            f.close()
            res['send'](text.replace("[[requests]]", str(webserver.info()['totalRequests'])))
        
        def getTest(req,res):
            res['send']("test")
        
        webserver.get('/',  getIndex)
        webserver.get('/test', getTest)
        webserver.listen(80, "0.0.0.0")
       

async def main():    
    tasks = [run()]
    await a.gather(*tasks)
    
a.run(main())
