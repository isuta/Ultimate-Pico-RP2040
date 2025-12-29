# autoplay_controller.py
import time
import random

class AutoPlayController:
    """自動再生制御を担当するクラス"""

    def __init__(self, random_scenarios, config):
        self.random_scenarios = random_scenarios
        
        # 時間管理
        self.last_user_interaction_time = time.ticks_ms()
        self.last_auto_play_time = time.ticks_ms()
        
        # 設定パラメータ
        self.IDLE_TIMEOUT_MS = getattr(config, "IDLE_TIMEOUT_MS", 300000)
        self.AUTO_PLAY_INTERVAL_MS = getattr(config, "AUTO_PLAY_INTERVAL_SECONDS", 60) * 1000
        
        # ワークショップ/デモモード設定
        self.WORKSHOP_MODE = getattr(config, "WORKSHOP_MODE", False)
        self.WORKSHOP_MODE_INTERVAL_MS = getattr(config, "WORKSHOP_MODE_INTERVAL_SECONDS", 3) * 1000

    def on_user_interaction(self):
        """ユーザー操作があったことを記録"""
        self.last_user_interaction_time = time.ticks_ms()

    def check_autoplay(self, is_playing, select_mode):
        """
        自動再生が必要かチェック
        
        Args:
            is_playing: 再生中かどうか
            select_mode: セレクトモード中かどうか
        
        Returns:
            str | None: 再生すべきシナリオ番号、または None
        """
        if is_playing or select_mode or not self.random_scenarios:
            return None
        
        now = time.ticks_ms()
        
        # ワークショップモード: 待ち時間なしで連続再生
        if self.WORKSHOP_MODE:
            auto_elapsed = time.ticks_diff(now, self.last_auto_play_time)
            if auto_elapsed >= self.WORKSHOP_MODE_INTERVAL_MS:
                scenario = random.choice(self.random_scenarios)
                print(f"[Workshop Mode] Scenario: {scenario}")
                self.last_auto_play_time = now
                return scenario
            return None
        
        # 通常モード: アイドルタイムアウト後に自動再生
        idle_elapsed = time.ticks_diff(now, self.last_user_interaction_time)
        auto_elapsed = time.ticks_diff(now, self.last_auto_play_time)

        if idle_elapsed >= self.IDLE_TIMEOUT_MS and auto_elapsed >= self.AUTO_PLAY_INTERVAL_MS:
            scenario = random.choice(self.random_scenarios)
            print(f"[AutoPlay] Scenario: {scenario}")
            self.last_auto_play_time = now
            return scenario
        
        return None

    def reset_autoplay_timer(self):
        """自動再生タイマーをリセット"""
        self.last_auto_play_time = time.ticks_ms()
