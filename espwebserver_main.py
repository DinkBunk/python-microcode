import ESPWebServer
import network
import machine
import os
from ota_updater import OTAUpdater

GPIO_NUM = 2 # Builtin led (D4)
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

ssid = 'MEB'
password = 'Biology$32'

# Disable AP interface
ap_if = network.WLAN(network.AP_IF)
if ap_if.active():
    ap_if.active(False)
  
# Connect to Wi-Fi if not connected
sta_if = network.WLAN(network.STA_IF)
if not ap_if.active():
    sta_if.active(True)
if not sta_if.isconnected():
    sta_if.connect(ssid, password)
    # Wait for connecting to Wi-Fi
    while not sta_if.isconnected(): 
        pass

# Show IP address
print("BUTTHOLE started @", sta_if.ifconfig()[0])
# Get pin object for controlling builtin LED
pin = machine.Pin(GPIO_NUM, machine.Pin.OUT)
pin.on() # Turn LED off (it use sinking input)

# Dictionary for template file
ledData = {
    "title":"Remote LED",
    "color":"red",
    "status":"Off",
    "switch":"on"
}

allPinsStatus = {

}

# Update information 
def updateInfo(socket):
    global ledData, color, status, switch
    ledData["color"] = "red" if pin.value() else "green"
    ledData["status"] = "Off" if pin.value() else "On"
    ledData["switch"] = "on" if pin.value() else "off"
    ESPWebServer.ok(
        socket, 
        "200",
        ledData["status"])

# Handler for path "/cmd?led=[on|off]"    
def handleCmd(socket, args):
    if 'led' in args:
        if args['led'] == 'on':
            pin.off()
        elif args['led'] == 'off':
            pin.on()
        updateInfo(socket)
    else:
        ESPWebServer.err(socket, "400", "Bad Request")

def handleFirmwareUpload(socket, args):
    received = socket.recv(BUFFER_SIZE).decode()
    filename, filesize = received.split(SEPARATOR)
    # remove absolute path if there is
    filename = os.path.basename(filename)
    # convert to integer
    filesize = int(filesize)
    with open(filename, "wb") as f:
      while True:
        # read 1024 bytes from the socket (receive)
        bytes_read = socket.recv(BUFFER_SIZE)
        if not bytes_read:    
            # nothing is received
            # file transmitting is done
            break
        # write to the file the bytes we just received
        f.write(bytes_read)
    updater = OTAUpdater(new_version_dir=filename)
    updater._delete_old_version()
    updater._install_new_version()


# handler for path "/switch" 
def handleSwitch(socket, args):
    pin.value(not pin.value()) # Switch back and forth
    updateInfo(socket)
    
# Start the server @ port 8899
ESPWebServer.begin(8899)

# Register handler for each path
# httpserver.onPath("/", handleRoot)
ESPWebServer.onPath("/cmd", handleCmd)
ESPWebServer.onPath("/switch", handleSwitch)
ESPWebServer.onPostPath("/update", handleFirmwareUpload)

# Setting the path to documents
ESPWebServer.setDocPath("/")

# Setting data for template
ESPWebServer.setTplData(ledData)

try:
    while True:
        # Let server process requests
        ESPWebServer.handleClient()
except:
    ESPWebServer.close()