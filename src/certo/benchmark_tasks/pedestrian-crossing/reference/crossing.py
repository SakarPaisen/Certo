class Crossing:
    _MIN_GREEN = 10
    _YELLOW = 3
    _RED = 7

    def __init__(self):
        self._state = "green"
        self._elapsed = 0
        self._waiting = False

    @property
    def state(self):
        return self._state

    @property
    def walk(self):
        return self._state == "red"

    def press_button(self):
        if self._state != "red":
            self._waiting = True

    def _change(self, state):
        self._state = state
        self._elapsed = 0
        if state == "red":
            self._waiting = False

    def tick(self):
        self._elapsed += 1
        if self._state == "green" and self._waiting and self._elapsed >= self._MIN_GREEN:
            self._change("yellow")
        elif self._state == "yellow" and self._elapsed >= self._YELLOW:
            self._change("red")
        elif self._state == "red" and self._elapsed >= self._RED:
            self._change("green")
