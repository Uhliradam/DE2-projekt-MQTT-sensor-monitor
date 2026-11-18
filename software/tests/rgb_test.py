"""
Test RGB
Ověří funguvaní RGB diody,jestli se zobrazuji vsecgny barvy a dane funkce 
"""
from machine import Pin
import time

LED_R_PIN = 12
LED_G_PIN = 13
LED_B_PIN = 14

STEP_S = 3     

COLORS = (
    ("cervena",  1, 0, 0),
    ("zelena",   0, 1, 0),
    ("modra",    0, 0, 1),
    ("zluta",    1, 1, 0),
    ("azurova",  0, 1, 1),
    ("fialova",  1, 0, 1),
    ("bila",     1, 1, 1),
)

red = Pin(LED_R_PIN, Pin.OUT)
green = Pin(LED_G_PIN, Pin.OUT)
blue = Pin(LED_B_PIN, Pin.OUT)


def set_color(r, g, b):
    red.value(r)
    green.value(g)
    blue.value(b)


try:
    print("=== Test RGB LED ===")
    for name, r, g, b in COLORS:
        print("Ma svitit:", name)
        set_color(r, g, b)
        time.sleep(STEP_S)

    print("Ma blikat zluta (jako pri pripojovani)")
    for _ in range(6):
        set_color(1, 1, 0)
        time.sleep(0.5)
        set_color(0, 0, 0)
        time.sleep(0.5)

finally:
    set_color(0, 0, 0)     
