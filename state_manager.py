# state_manager.py
import random
from button_handler import ButtonHandler
from playback_manager import PlaybackManager
from autoplay_controller import AutoPlayController

class StateManager:
    """システム全体の状態統合を担当する軽量調整役"""

    def __init__(self, dm, vc, scenarios_data, valid_scenarios, random_scenarios, config):
        # 外部リソース
        self.dm = dm
        self.vc = vc
        self.valid_scenarios = valid_scenarios

        # サブコンポーネント
        self.button_handler = ButtonHandler(config)
        self.playback_manager = PlaybackManager(scenarios_data)
        self.autoplay_controller = AutoPlayController(random_scenarios, config)

        # セレクトモード状態
        self.selected_index = 0
        self.selected_scenario = valid_scenarios[0] if valid_scenarios else "1"
        self.select_mode = False  # 起動直後は必ず通常モード

        # 表示系
        self.current_display = ""
        self.push_message = "Push the button"
        self.select_mode_message = "Select Mode"

        # 再生完了コールバックを設定
        self.playback_manager.set_complete_callback(self._on_play_complete)

        # OLED初期表示
        self.dm.push_message([self.push_message])
        self.current_display = self.push_message

    # ----------------------------------------------------------------------
    # OLED表示の更新
    # ----------------------------------------------------------------------
    def update_oled_select_mode_display(self):
        """セレクトモード表示を更新"""
        self.dm.push_message([self.select_mode_message, self.selected_scenario])
        self.current_display = self.selected_scenario

    def _on_play_complete(self):
        """再生完了時のコールバック"""
        print("再生が終了しました。")
        
        if self.select_mode:
            self.update_oled_select_mode_display()
        else:
            if self.current_display != self.push_message:
                self.dm.push_message([self.push_message])
                self.current_display = self.push_message

    # ----------------------------------------------------------------------
    # ボタン処理（ButtonHandler への委譲）
    # ----------------------------------------------------------------------
    def handle_button(self, button):
        """ボタン入力を処理"""
        # ButtonHandler でイベント検出
        result = self.button_handler.update(button, self.select_mode, self.playback_manager.is_busy())
        event = result['event']
        
        # ユーザー操作を記録
        if event:
            self.autoplay_controller.on_user_interaction()
        
        # イベント別処理
        if event == 'enter_select_mode':
            self.select_mode = True
            print("=== Select Mode Start ===")
            self.update_oled_select_mode_display()
        
        elif event == 'short_press':
            # 通常モードでランダム再生
            scenario = self.autoplay_controller.random_scenarios
            if scenario:
                scenario = random.choice(scenario)
                print(f"Random Play Scenario: {scenario}")
                self.playback_manager.start_scenario(scenario, self.dm)
        
        elif event == 'stop':
            # 再生中断
            self.playback_manager.stop_playback(self.dm)
        
        elif event == 'select_confirm':
            # セレクトモードで決定
            scenario = self.valid_scenarios[self.selected_index]
            print(f"Play Scenario: {scenario}")
            self.playback_manager.start_scenario(scenario, self.dm)
        
        # セレクトモード内の選択更新
        if self.select_mode:
            selection_change = self.button_handler.get_selection_change()
            if selection_change != 0:
                num_scenarios = len(self.valid_scenarios)
                if selection_change == 1:
                    self.selected_index = (self.selected_index + 1) % num_scenarios
                elif selection_change == -1:
                    self.selected_index = (self.selected_index - 1 + num_scenarios) % num_scenarios
                
                self.selected_scenario = self.valid_scenarios[self.selected_index]
                print(f"Selected Scenario: {self.selected_scenario}")
                self.update_oled_select_mode_display()

    # ----------------------------------------------------------------------
    # 再生管理（PlaybackManager への委譲）
    # ----------------------------------------------------------------------
    def update_playback(self):
        """再生状態の更新"""
        self.playback_manager.update()

    # ----------------------------------------------------------------------
    # 自動再生チェック（AutoPlayController への委譲）
    # ----------------------------------------------------------------------
    def check_idle_autoplay(self):
        """アイドル時の自動再生をチェック"""
        scenario = self.autoplay_controller.check_autoplay(
            self.playback_manager.is_busy(),
            self.select_mode
        )
        
        if scenario:
            self.playback_manager.start_scenario(scenario, self.dm)

    # ----------------------------------------------------------------------
    # 後方互換性のためのプロパティ
    # ----------------------------------------------------------------------
    @property
    def is_playing(self):
        """再生中かどうか（互換性のため）"""
        return self.playback_manager.is_busy()

    @property
    def stop_flag(self):
        """停止フラグ（互換性のため）"""
        return self.playback_manager.stop_flag
