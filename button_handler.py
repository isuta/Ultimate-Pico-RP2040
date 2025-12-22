# button_handler.py
import time

class ButtonHandler:
    """ボタン入力処理を担当するクラス"""

    def __init__(self, config):
        # 入力系
        self.button_pressed = False
        self.press_time = 0
        self.release_time = 0
        self.click_count = 0
        self.last_click_time = 0
        self.last_press_time = 0
        
        # 設定パラメータ
        self.BUTTON_SHORT_PRESS_MS = getattr(config, "BUTTON_SHORT_PRESS_MS", 500)
        self.BUTTON_LONG_PRESS_MS = getattr(config, "BUTTON_LONG_PRESS_MS", 1000)
        self.BUTTON_DOUBLE_CLICK_INTERVAL_MS = getattr(config, "BUTTON_DOUBLE_CLICK_INTERVAL_MS", 500)

    def update(self, button, select_mode, is_playing):
        """
        ボタン状態を更新し、検出されたイベントを返す
        
        戻り値:
            dict: {
                'event': 'short_press' | 'long_press' | 'select_click' | 'select_confirm' | 'stop' | None,
                'press_duration': int (ms),
                'timestamp': int (ms)
            }
        """
        now = time.ticks_ms()
        current_state = button.value()  # 押下:1, 離:0 の想定
        event = None
        press_duration = 0

        # 押下開始
        if current_state == 1 and not self.button_pressed:
            self.button_pressed = True
            self.press_time = now
            self.last_press_time = now

        # 長押し検出（通常モード → セレクトモード）
        elif current_state == 1 and self.button_pressed:
            press_duration = time.ticks_diff(now, self.press_time)
            if press_duration >= self.BUTTON_LONG_PRESS_MS and not select_mode and not is_playing:
                event = 'enter_select_mode'

        # 離した瞬間
        elif current_state == 0 and self.button_pressed:
            self.button_pressed = False
            self.release_time = now
            press_duration = time.ticks_diff(now, self.press_time)

            if select_mode:
                # セレクトモード内の短押し・長押し判定
                if press_duration < self.BUTTON_SHORT_PRESS_MS:
                    self.click_count += 1
                    self.last_click_time = now
                    event = 'select_click'
                elif press_duration >= self.BUTTON_LONG_PRESS_MS:
                    event = 'select_confirm'
            else:
                # 通常モードの短押しによるランダム再生
                if press_duration < self.BUTTON_SHORT_PRESS_MS and not is_playing:
                    event = 'short_press'
                elif is_playing:
                    event = 'stop'

        return {
            'event': event,
            'press_duration': press_duration,
            'timestamp': now
        }

    def get_selection_change(self):
        """
        セレクトモード内のクリック連打を検出し、選択変更を返す
        
        戻り値:
            int: 1 (次へ), -1 (前へ), 0 (変更なし)
        """
        now = time.ticks_ms()
        
        if self.click_count > 0:
            if time.ticks_diff(now, self.last_click_time) > self.BUTTON_DOUBLE_CLICK_INTERVAL_MS:
                clicks = self.click_count
                self.click_count = 0
                
                if clicks == 1:
                    return 1  # 次へ
                elif clicks == 2:
                    return -1  # 前へ
                else:
                    return 1  # 3回以上は次へ
        
        return 0  # 変更なし

    def reset(self):
        """ボタン状態をリセット"""
        self.button_pressed = False
        self.click_count = 0
