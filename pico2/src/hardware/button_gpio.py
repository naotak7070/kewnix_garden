# hardware/button_gipo.py
from machine import Pin
from interfaces.button_interface import ButtonInterface

class ButtonGpio(ButtonInterface):
    def __init__(self, pin_number):
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_DOWN)

    def read(self):
        return self.pin.value()

    def is_pressed(self) -> bool:
            return self.pin.value() == 0