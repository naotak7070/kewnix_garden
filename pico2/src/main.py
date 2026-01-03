from logic.multipump_controller import MultiPumpController
from display.display_manager import DisplayManager
from hardware.button_gpio import ButtonGpio
import time

def main():
    # ボタン設定
    buttonA = ButtonGpio(pin_number=20)
    buttonB = ButtonGpio(pin_number=21)

    # ディスプレイ
    display = DisplayManager(use_mock=True)

    # ポンプ設定: pin, ON(ms), OFF(ms)
    min1 = 60 * 1000
    h1 = 60 * min1
    min15 = 15 * min1
    sec5 = 5 * 1000

    pump_configs = [
        (6, sec5, h1),
        (7, sec5, min15),
        (8, sec5, min15),
        (9, sec5, min15),
        (10, sec5, min15),
        # (11, sec5, min15),
        # (12, sec5, min15),
        # (13, sec5, min15),
    ]

    controller = MultiPumpController(pump_configs, display)
    controller.begin()

    lastA = lastB = 1

    while True:
        currentA = buttonA.read()
        currentB = buttonB.read()

        if lastA == 1 and currentA == 0:
            controller.switch_mode("interval")

        if lastB == 1 and currentB == 0:
            if controller.mode != "manual":
                controller.switch_mode("manual")
            controller.handle_manual()

        lastA = currentA
        lastB = currentB

        controller.update()
        time.sleep_ms(100)

main()
