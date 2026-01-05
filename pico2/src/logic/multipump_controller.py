import time
from machine import Pin

class MultiPumpController:
    def __init__(self, pump_configs, display_manager):
        self.display = display_manager

        # 有効(enabled)なポンプだけを抽出して管理
        # 内部構造: [{'pin_obj': Pin, 'config': dict, 'next_trigger': int}, ...]
        self.pumps = []
        
        for cfg in pump_configs:
            # 辞書キー 'enabled' を確認。デフォルトはTrue扱い。
            if cfg.get('enabled', True):
                self.pumps.append({
                    'pin_obj': Pin(cfg['pin'], Pin.OUT),
                    'config': cfg,
                    'next_trigger': 0
                })

        self.active_index = -1
        self.active_end = 0
        self.pending = [] 

        self.mode = "interval"
        self.manual_step = 0
        self.manual_state = [False] * len(self.pumps)
        self.last_display_refresh = 0

    def begin(self):
        now = time.ticks_ms()
        for p in self.pumps:
            p['pin_obj'].value(0)
            p['next_trigger'] = now
        self.stop_all()
        self.last_display_refresh = now
        self.update_display(now)

    def stop_all(self):
        for i, p in enumerate(self.pumps):
            p['pin_obj'].value(0)
            self.manual_state[i] = False
        self.active_index = -1
        self.pending.clear()

    def switch_mode(self, new_mode):
        self.mode = new_mode
        self.stop_all()
        now = time.ticks_ms()
        if new_mode == "interval":
            for p in self.pumps:
                p['next_trigger'] = now
            self.update_display(now)
        else:
            self.update_display(now)

    def update(self):
        now = time.ticks_ms()
        if self.mode == "interval":
            self.handle_interval(now)
            if time.ticks_diff(now, self.last_display_refresh) >= 1000:
                self.update_display(now)
                self.last_display_refresh = now
        elif self.mode == "manual":
            pass


    def update_display(self, now):
        # DisplayManagerに渡すための簡易リスト作成
        simple_configs = []
        triggers = []
        for p in self.pumps:
            cfg = p['config']
            simple_configs.append((cfg['pin'], cfg['high_ms'], cfg['low_ms']))
            triggers.append(p['next_trigger'])

        if self.mode == "interval":
            self.display.show_interval_mode(self.active_index, triggers, simple_configs, now)
        else:
            # ▼ 修正: 現在フォーカスすべきピンのインデックスを計算
            count = len(self.pumps)
            focused_idx = 0
            
            if count > 0:
                # manual_step は「次の操作」を指しているので、-1 して「今の操作対象」に戻す
                current_step = (self.manual_step - 1)
                
                # マイナスになった場合（初期状態など）は0にする
                if current_step < 0: current_step = 0
                
                # ステップからピン番号(インデックス)を逆算
                # step 0,1 -> idx 0 / step 2,3 -> idx 1 ...
                focused_idx = (current_step % (count * 2)) // 2

            # フォーカス位置を渡して表示更新
            self.display.show_manual_mode(self.manual_state, simple_configs, focused_index=focused_idx)


    def handle_interval(self, now):
        if self.active_index >= 0 and now >= self.active_end:
            # ポンプ停止
            self.pumps[self.active_index]['pin_obj'].value(0)
            # 次回起動時刻を設定
            low_ms = self.pumps[self.active_index]['config']['low_ms']
            self.pumps[self.active_index]['next_trigger'] = self.active_end + low_ms
            self.active_index = -1

        for i, p in enumerate(self.pumps):
            if i != self.active_index and now >= p['next_trigger'] and i not in self.pending:
                self.pending.append(i)

        if self.active_index == -1 and self.pending:
            idx = self.pending.pop(0)
            self.pumps[idx]['pin_obj'].value(1)
            high_ms = self.pumps[idx]['config']['high_ms']
            self.active_index = idx
            self.active_end = now + high_ms

    def handle_manual(self):
        count = len(self.pumps)
        if count == 0: return

        step = self.manual_step % (count * 2)
        idx = step // 2
        is_on = (step % 2 == 0)

        self.pumps[idx]['pin_obj'].value(1 if is_on else 0)
        self.manual_state[idx] = is_on
        self.manual_step = (step + 1) % (count * 2)
        self.update_display(time.ticks_ms())