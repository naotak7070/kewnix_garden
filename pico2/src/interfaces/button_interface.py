# interface/button_interface.py
class ButtonInterface:
    def is_pressed(self)->bool:
        # return button is pressed or not
        raise NotImplementedError(
            "You need to implement the is_pressed() method.Make sure to define the is_pressed() function."
            )