from machine import Pin
from time import sleep_ms

BUTTON_PIN = 15

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

print("Push Button Test")
print("Press and release the button.")
print("Press Ctrl+C to stop the test.")

previous_state = button.value()
press_count = 0

try:
    while True:
        current_state = button.value()

        if current_state != previous_state:
            sleep_ms(30)
            current_state = button.value()

            if current_state != previous_state:
                if current_state == 0:
                    press_count += 1
                    print("Button pressed:", press_count)
                else:
                    print("Button released")

                previous_state = current_state

        sleep_ms(10)

except KeyboardInterrupt:
    print("Test finished.")
    print("Total button presses:", press_count)
