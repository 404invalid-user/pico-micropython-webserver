import network
import socket
import time

from machine import Pin


def CleanRequest(req):
    sep = req.replace("\r\n"," ").replace("\\r\\n"," ").split(" ")

    extras = []
    last_extra = 0
    for x in range(len(sep)):
        if ":" in sep[x] and sep[x].find("://") == -1:
            try:
                extras.append({sep[x].replace(":", ""): sep[x+1]})
                last_extra = x+1
            except:
                print()
                
    post_data = sep[last_extra+1:]
    post_data = " ".join(post_data).replace(' ', '').replace("'","")
    
    try:
        if "?" in sep[1]:
            return {
                "method": sep[0].replace("b'", ""),
                "route": sep[1].split('?')[0],
                "params": "?"+sep[1].split('?')[1],
                "extras":extras,
                "post_data": post_data}
        else:
            return {
                "method": sep[0].replace("b'", ""),
                "route": sep[1].split('?')[0],
                "params": "",
                "extras":extras,
                "post_data":post_data}
    except:
        #hmmm
        return {
                "method": "GET",
                "route": "/",
                "params": "",
                "extras":{},
                "post_data":""}

led = Pin("LED", Pin.OUT)
led.value(0)

def FlashLed():
    global led
    led.value(1)
    time.sleep(0.02)
    led.value(0)
    


class WebServer:
    def __init__(self):
        self.total_requests = 0
        self.post_requests = 0
        self.get_requests = 0
        
    #call back function for get requests
    get_callbacks = None    
    def get(self, event_name, callback):
        if self.get_callbacks is None:
            self.get_callbacks = {}
        
        if event_name not in self.get_callbacks:
            self.get_callbacks[event_name] = [callback]
        else:
            self.get_callbacks[event_name].append(callback)
    
    #call back function for post requests
    post_callbacks = None
    def post(self, event_name, callback):
        if self.post_callbacks is None:
            self.post_callbacks = {}
        
        if event_name not in self.post_callbacks:
            self.post_callbacks[event_name] = [callback]
        else:
            self.post_callbacks[event_name].append(callback)
            
    
    def info(self):
        return {"getRequests": self.get_requests, "totalRequests": self.total_requests, "PostRequests": self.post_requests}
                
    def listen(self, port, host):
        host_name = "0.0.0.0"
        if host:
            host_name = host
        self.addr = socket.getaddrinfo(host, port)[0][-1]
        self.socket = socket.socket()
        self.socket.bind(self.addr)
        self.socket.listen(1)
        print("listening on "+host+":"+str(port))
        
        while True:
            try:
                cl, addr = self.socket.accept()
                print('client connected from', addr)
                FlashLed()
                self.total_requests += 1
                request = cl.recv(1024)
                
                request = str(request)
                clean_request = CleanRequest(request)
                
                print(str(clean_request))
                
                def SendHTML(data):
                    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                    cl.send(data)
                    return cl.close()
                    
                def SendJson(data):
                    cl.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
                    cl.send(data)
                    return cl.close()
                    
                    
                #handle get requests
                
                if clean_request['method'] == "GET":
                    self.get_requests += 1
                    if self.get_callbacks is not None and clean_request['route'] in self.get_callbacks:
                        for callback in self.get_callbacks[clean_request['route']]:
                            callback({}, {'send': SendHTML, 'json': SendJson})
                    
                #handle post requests
                elif clean_request['method'] == "POST":
                    self.post_requests += 1
                    if self.post_callbacks is not None and clean_request['route'] in self.post_callbacks:
                        for callback in self.post_callbacks[clean_request['route']]:
                            callback({}, {'send': SendHTML, 'json': SendJson})
                
                
    
            except OSError as e:
                cl.close()
                print('connection closed')
