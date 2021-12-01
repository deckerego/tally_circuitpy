# TallyCircuitPy

A network controlled tally light for cameras, intended for control by
[TallyOBS](https://github.com/deckerego/tally_obs)
but extensible enough to use for whatever purposes you like.


## Installing

When installing for the first time, extract the latest
[tally_circuitpy.zip](https://github.com/deckerego/tally_circuitpy/releases/latest)
into a directory, then copy the contents of that extracted archive
into the CIRCUITPY drive that appears when you plug in your Macropad.
Ensure that the contents of the `lib/` subdirectory are also copied - these are
the precompiled Adafruit libraries that power the Macropad.

tally_circuitpy requires CircuitPython 7.0, which can be downloaded at
https://circuitpython.org/downloads and can be flashed according to your
board's instructions. Many ESP32-S2 boards follow similar ESPTool instructions as listed
[on Adafruit's Metro ESP32-S2](https://learn.adafruit.com/adafruit-metro-esp32-s2/rom-bootloader)
learn page. If you are flashing with the ESPTool, make sure to flash with the
`.bin` file (_not_ the `.uf2` file).


## Configuration

Once the files have been copied over, update the `secrets.py` file in the
CIRCUITPY drive to contain your WiFi SSID and PSK. If the activity LED
blinks rapidly, that indicates your tally light cannot connect to WiFi.
Double-check that you have a valid SSID and PSK for a 2.4GHz WiFi network
specified in `secrets.py`.

Configuration settings are stored in the `settings.py` file, including the
maximum LED brightness allowed. Some devices cannot run at over 50% brightness
without heat sinks, and so a max value can be enforced so
devices will not overheat.


## Required Libraries

All required libraries are supplied through the release .ZIP files. If you want
to install directly from the repository, you will need the
[ampule.py](https://github.com/deckerego/ampule) and the
[Adafruit NeoPixel](https://github.com/adafruit/Adafruit_CircuitPython_Bundle)
libraries installed into the `lib/` directory.


## Hardware

TallyCircuitPy has been tested with the
[PixelWing ESP32-S2 RGB Matrix](https://www.tindie.com/products/oakdevtech/pixelwing-esp32-s2-rgb-matrix/)
but should work with any device that supports CircuitPython 7's `wifi libraries`.

There is also an enclosure supplied with TallyCircuitPy that can be 3D printed.
It is available from this repository
or via [Thingiverse](https://www.thingiverse.com/thing:4962628).


## The Tally Light API

A web service is provided to expose LED values through an HTTP interface.
This controls color and brightness, and will monitor the on/off switch
(if available) to shut down the light in an orderly fashion.

An HTTP interface is provided that allows for color control and brightness
to be specified remotely. As an example:

    http://192.168.1.1:7413/set?color=AA22FF&brightness=0.3

Would set the NeoPixels to be purple across all LEDs, at 30% brightness.

The status of the LEDs are available as:

    http://192.168.1.1:7413/status
