
import gc
import network
import micropython

micropython.alloc_emergency_exception_buf(300)
 
import esp
esp.osdebug(None)

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

gc.collect()


