import time
import board
from digitalio import DigitalInOut, Direction

led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
led.value = False
_blinking = False

def blink(sleep):
    _blinking = True
    while _blinking:
        led.value = not led.value
        time.sleep(sleep)

def _enabled(value):
    _blinking = False
    led.value = value;

def on():
    _enabled(True)

def off():
    _enabled(False)
