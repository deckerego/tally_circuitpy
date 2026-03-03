import socketpool
import ampule
import light
import led
import time
import board
import busio
import digitalio

# Try to import W5500 ethernet
try:
    import adafruit_wiznet5k.adafruit_wiznet5k as wiznet5k
    ETHERNET_AVAILABLE = True
    eth = None  # Will be initialized later
except ImportError:
    ETHERNET_AVAILABLE = False

try:
    import wifi
    WIFI_AVAILABLE = True
except ImportError:
    WIFI_AVAILABLE = False

# Track which network interface is active
network_interface = None

headers = {
    "Content-Type": "application/json; charset=UTF-8",
    "Access-Control-Allow-Origin": '*',
    "Access-Control-Allow-Methods": 'GET, POST',
    "Access-Control-Allow-Headers": 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
}

@ampule.route("/dashboard")
def dashboard(request):
    document = ''
    with open("/dashboard.html", "r") as reader:
        document += reader.read()
    return (200, {"Content-Type": "text/html; charset=utf-8"}, document)

@ampule.route("/set")
def light_set(request):
    color_hex = request.params["color"]
    bright_pct = request.params["brightness"]

    red = int(color_hex[0:2], 16)
    green = int(color_hex[2:4], 16)
    blue = int(color_hex[4:6], 16)
    brightness = float(bright_pct or 0.5)

    light.setBrightness(brightness)
    light.goToColor(red, green, blue)

    body = _to_json(red, green, blue, brightness)
    return (200, headers, body)

@ampule.route("/status")
def light_status(request):
    red, green, blue = light.getColor()
    brightness = light.getBrightness()
    body = _to_json(red, green, blue, brightness)
    return (200, headers, body)

def _to_json(r, g, b, bright):
    # Priority: secrets hostname > network interface hostname > "unknown"
    if "hostname" in secrets:
        hostname = secrets["hostname"]
    else:
        hostname = "unknown"
        
        if WIFI_AVAILABLE and network_interface == wifi:
            try:
                hostname = wifi.radio.hostname
            except:
                pass
        elif ETHERNET_AVAILABLE and network_interface == eth:
            try:
                hostname = eth.hostname
            except:
                pass
    
    return '{ "hostname": "%s", "red": %i, "green": %i, "blue": %i, "brightness": %f }' % (hostname, r, g, b, bright)

def _ethernet_connect():
    """Attempt to connect via W5500 ethernet."""
    global network_interface, eth
    try:
        if not ETHERNET_AVAILABLE:
            return False
        
        led.on()
        print("Attempting W5500 ethernet connection...")
        
        # Initialize SPI bus for W5500
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        
        # Setup chip select and reset pins
        # These are typical pins; adjust based on your board configuration
        cs = digitalio.DigitalInOut(board.D10)
        reset = digitalio.DigitalInOut(board.D9)
        
        # Initialize W5500
        eth = wiznet5k.WIZNET5K(spi, cs, reset=reset)
        
        # Attempt to connect to network
        eth.connect()
        
        print("W5500 ethernet interface ready")
        network_interface = eth
        return True
    except Exception as e:
        print("W5500 ethernet not available or failed: %s" % e)
        network_interface = None
        eth = None
        return False

def _wifi_connect(ssid, password):
    """Attempt to connect via WiFi."""
    global network_interface
    if not WIFI_AVAILABLE:
        print("WiFi not available")
        return False
    
    max_retries = 3
    sleep = 0.5
    retries = 0
    last_exception = BaseException("WiFi Connect Failure")

    print("MAC: ", [hex(i) for i in wifi.radio.mac_address])
    while retries <= max_retries:
        try:
            led.on()
            print("Connecting to %s..." % ssid)
            wifi.radio.connect(ssid, password)
            network_interface = wifi
            return True
        except Exception as e:
            led.off()
            print("Will retry connection to %s: %s" % (ssid, e))
            last_exception = e
            retries += 1
            time.sleep(sleep * retries)
    raise last_exception

def _socket_build():
    """Build socket pool using the active network interface."""
    led.off()
    if not network_interface:
        raise RuntimeError("No network interface available")
    
    pool = socketpool.SocketPool(network_interface)
    socket = pool.socket()
    socket.bind(['0.0.0.0', 7413])
    socket.listen(1)
    socket.setblocking(True)
    
    # Print IP address based on interface type
    if ETHERNET_AVAILABLE and network_interface == eth:
        print("IPv4 Addr (W5500 Ethernet):", eth.ipv4_address)
    elif WIFI_AVAILABLE and network_interface == wifi:
        print("IPv4 Addr (WiFi):", wifi.radio.ipv4_address)
    
    led.on()
    return socket

### BEGIN Initialize Tally Light

led.on()

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets not found in secrets.py")
    led.blink(0.25)
    raise

socket = None
while True:
    # Check if we need to reconnect
    need_reconnect = False
    
    if ETHERNET_AVAILABLE and network_interface == eth:
        # Check W5500 ethernet status
        try:
            if not eth.link_status():
                need_reconnect = True
        except:
            need_reconnect = True
    elif WIFI_AVAILABLE and network_interface == wifi:
        # Check WiFi status
        if not wifi.radio.ap_info or not wifi.radio.ap_info.channel:
            need_reconnect = True
    else:
        # No connection yet
        need_reconnect = True
    
    if need_reconnect:
        if socket: 
            socket.close()
            socket = None

        connected = False
        
        # Try ethernet first
        if ETHERNET_AVAILABLE:
            if _ethernet_connect():
                connected = True
        
        # Fall back to WiFi if ethernet not available or failed
        if not connected and WIFI_AVAILABLE:
            try:
                _wifi_connect(secrets["ssid"], secrets["password"])
                connected = True
            except Exception as e:
                print("Error connecting to WiFi:", e)
                led.blink(0.1)
                raise
        
        if not connected:
            print("Error: No network interface available")
            led.blink(0.5)
            raise RuntimeError("Failed to connect to any network interface")

        socket = _socket_build()
        light.test()

    if socket: 
        ampule.listen(socket)
    else:
        print("No socket available!")
        led.blink(0.5)
