import time
from machine import Pin

class MultiPumpController:
    def __init__(self, pump_configs, display_manager):
        self.configs = pump_configs  # [(pin, high_ms, low_ms), ...]
        self.channel_count = len(pump_configs)
        self.pins = [Pin(cfg[0], Pin.OUT) for cfg in pump_configs]
        self.display = display_manager

        self.active_ch = -1
        self.active_end = 0
        self.next_triggers = [0] * self.channel_count
        self.pending = []

        self.mode = "interval"
        self.manual_step = 0
        self.manual_state = [False] * self.channel_count

        self.last_display_refresh = 0

    def begin(self):
        now = time.ticks_ms()
        for i in range(self.channel_count):
            self.pins[i].value(0)
            self.next_triggers[i] = now
        self.stop_all()
        self.last_display_refresh = now
        self.display.show_interval_mode(self.active_ch, self.next_triggers, self.configs, now)

    def stop_all(self):
        for i in range(self.channel_count):
            self.pins[i].value(0)
            self.manual_state[i] = False
        self.active_ch = -1
        self.pending.clear()

    def switch_mode(self, new_mode):
        self.mode = new_mode
        self.stop_all()
        now = time.ticks_ms()
        if new_mode == "interval":
            for i in range(self.channel_count):
                self.next_triggers[i] = now
            self.display.show_interval_mode(self.active_ch, self.next_triggers, self.configs, now)
        else:
            self.display.show_manual_mode(self.manual_state, self.configs)

    def update(self):
        now = time.ticks_ms()
        if self.mode == "interval":
            self.handle_interval(now)
            if time.ticks_diff(now, self.last_display_refresh) >= 1000:
                self.display.show_interval_mode(self.active_ch, self.next_triggers, self.configs, now)
                self.last_display_refresh = now
        elif self.mode == "manual":
            self.display.show_manual_mode(self.manual_state, self.configs)


                
    def handle_interval(self, now):
        if self.active_ch >= 0 and now >= self.active_end:
            self.pins[self.active_ch].value(0)
            _, high_ms, low_ms = self.configs[self.active_ch]
            self.next_triggers[self.active_ch] = self.active_end + low_ms
            self.active_ch = -1

        for i in range(self.channel_count):
            if i != self.active_ch and now >= self.next_triggers[i] and i not in self.pending:
                self.pending.append(i)

        if self.active_ch == -1 and self.pending:
            ch = self.pending.pop(0)
            self.pins[ch].value(1)
            _, high_ms, _ = self.configs[ch]
            self.active_ch = ch
            self.active_end = now + high_ms

    def handle_manual(self):
        step = self.manual_step % (self.channel_count * 2)
        ch = step // 2
        is_on = (step % 2 == 0)
        self.pins[ch].value(1 if is_on else 0)
        self.manual_state[ch] = is_on
        self.manual_step = (step + 1) % (self.channel_count * 2)
