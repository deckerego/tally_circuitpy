import board
import wifi
import socketpool
import ampule
import light
import led

headers = {
    "Content-Type": "application/json; charset=UTF-8",
    "Access-Control-Allow-Origin": '*',
    "Access-Control-Allow-Methods": 'GET, POST',
    "Access-Control-Allow-Headers": 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
}

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


### BEGIN Initialize Tally Light

led.on()

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets not found in secrets.py")
    led.blink(0.25)
    raise

try:
    print("Connecting to %s..." % secrets["ssid"])
    print("MAC: ", [hex(i) for i in wifi.radio.mac_address])
    wifi.radio.connect(secrets["ssid"], secrets["password"])
except:
    print("Error connecting to WiFi")
    led.blink(0.1)
    raise

led.off()
pool = socketpool.SocketPool(wifi.radio)
socket = pool.socket()
socket.bind(['0.0.0.0', 7413])
socket.listen(5)
print("Connected to %s, IPv4 Addr: " % secrets["ssid"], wifi.radio.ipv4_address)

led.on()
light.test()

while True:
    ampule.listen(socket)
