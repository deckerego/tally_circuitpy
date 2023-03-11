import board
import wifi
import socketpool
import ampule
import light
import led
import time

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
    hostname = secrets["hostname"] if "hostname" in secrets else wifi.radio.hostname
    return '{ "hostname": "%s", "red": %i, "green": %i, "blue": %i, "brightness": %f }' % (hostname, r, g, b, bright)

def _wifi_connect(ssid, password):
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
            return True
        except Exception as e:
            led.off()
            print("Will retry connection to %s: %s" % (ssid, e))
            last_exception = e
            retries += 1
            time.sleep(sleep * retries)
    raise last_exception

def _socket_build():
    led.off()
    pool = socketpool.SocketPool(wifi.radio)
    socket = pool.socket()
    socket.bind(['0.0.0.0', 7413])
    socket.listen(1)
    socket.setblocking(True)
    print("IPv4 Addr:", wifi.radio.ipv4_address)
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
    if not wifi.radio.ap_info or not wifi.radio.ap_info.channel:
        if socket: socket.close()

        try:
            _wifi_connect(secrets["ssid"], secrets["password"])
        except Exception as e:
            print("Error connecting to WiFi:", e)
            led.blink(0.1)
            raise

        socket = _socket_build()
        light.test()

    if socket: 
        ampule.listen(socket)
    else:
        print("No socket available!")
        led.blink(0.5)
