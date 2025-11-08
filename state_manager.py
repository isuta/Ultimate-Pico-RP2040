# state_manager.py
import time
import random
import effects
import onboard_led
import _thread

class StateManager:
    """システム全体の状態とボタン操作を管理するクラス"""

    def __init__(self, dm, vc, scenarios_data, valid_scenarios, random_scenarios, config):
        # 外部リソース
        self.dm = dm
        self.vc = vc
        self.scenarios_data = scenarios_data
        self.valid_scenarios = valid_scenarios
        self.random_scenarios = random_scenarios

        # 状態管理変数
        self.selected_index = 0
        self.selected_scenario = valid_scenarios[0] if valid_scenarios else "1"
        self.select_mode = False  # 起動直後は必ず通常モード
        self.is_playing = False
        self.stop_flag = [False]
        self.current_play_scenario = None

        # 入力系
        self.button_pressed = False
        self.press_time = 0
        self.release_time = 0
        self.click_count = 0
        self.last_click_time = 0
        self.last_press_time = 0

        # 時間管理
        self.last_user_interaction_time = time.ticks_ms()
        self.last_auto_play_time = time.ticks_ms()

        # 表示系
        self.current_display = ""
        self.push_message = "Push the button"
        self.select_mode_message = "Select Mode"

        # 設定パラメータ
        self.IDLE_TIMEOUT_MS = getattr(config, "IDLE_TIMEOUT_MS", 300000)
        self.POLLING_DELAY_MS = getattr(config, "MAIN_LOOP_POLLING_MS", 10)
        self.AUTO_PLAY_INTERVAL_MS = getattr(config, "AUTO_PLAY_INTERVAL_SECONDS", 60) * 1000
        
        # ボタン操作の閾値
        self.BUTTON_SHORT_PRESS_MS = getattr(config, "BUTTON_SHORT_PRESS_MS", 500)
        self.BUTTON_LONG_PRESS_MS = getattr(config, "BUTTON_LONG_PRESS_MS", 1000)
        self.BUTTON_DOUBLE_CLICK_INTERVAL_MS = getattr(config, "BUTTON_DOUBLE_CLICK_INTERVAL_MS", 500)

        # OLED初期表示
        self.dm.push_message([self.push_message])
        self.current_display = self.push_message

    # ----------------------------------------------------------------------
    # OLED表示の更新
    # ----------------------------------------------------------------------
    def update_oled_select_mode_display(self):
        self.dm.push_message([self.select_mode_message, self.selected_scenario])
        self.current_display = self.selected_scenario

    # ----------------------------------------------------------------------
    # シナリオ再生
    # ----------------------------------------------------------------------
    def start_scenario_in_thread(self, num):
        """スレッドで再生（起動失敗を安全にハンドル）"""
        def thread_func():
            try:
                onboard_led.turn_on()
                print(f"Onboard LED: ON (Scenario {num} started)")
                effects.playEffectByNum(self.scenarios_data, num, self.stop_flag)
            except OSError as e:
                # ハードウェア関連エラー（GPIO, I2C, UART等）
                print(f"[Hardware Error] Scenario {num} failed: {e}")
                self.dm.push_message(["Hardware", "Error"])
            except KeyError as e:
                # シナリオデータの不整合
                print(f"[Data Error] Invalid scenario key {num}: {e}")
                self.dm.push_message(["Invalid", "Scenario"])
            except MemoryError as e:
                # メモリ不足
                print(f"[Memory Error] Out of memory in scenario {num}: {e}")
                self.dm.push_message(["Memory", "Error"])
            except Exception as e:
                # その他の予期しないエラー
                print(f"[Error] Scenario thread failed: {e}")
                # スタックトレースを出力（デバッグ用）
                import sys
                sys.print_exception(e)
                self.dm.push_message(["Playback", "Error"])
            finally:
                # 再生終了処理（例外時でも呼ぶ）
                try:
                    self.play_complete_callback()
                except Exception as e2:
                    print(f"[Critical Error] play_complete_callback failed: {e2}")
                    import sys
                    sys.print_exception(e2)

        # ガード：二重起動防止（念のため）および起動時の例外処理
        if self.is_playing:
            print("[Debug] start_scenario_in_thread: already playing — ignore")
            return

        # 一旦フラグを立て、スレッド起動に失敗したら戻す
        self.is_playing = True
        self.stop_flag[0] = False
        try:
            _thread.start_new_thread(thread_func, ())
        except OSError as e:
            # スレッド起動失敗（core1 in use, メモリ不足など）
            print(f"[Thread Error] Thread start failed: {e}")
            self.dm.push_message(["Thread", "Error"])
            # 状態を元に戻す
            self.is_playing = False
            self.stop_flag[0] = True
        except RuntimeError as e:
            # ランタイムエラー
            print(f"[Runtime Error] Thread creation failed: {e}")
            self.dm.push_message(["System", "Error"])
            self.is_playing = False
            self.stop_flag[0] = True
        except Exception as e:
            print(f"[Unexpected Error] Thread start error: {e}")
            import sys
            sys.print_exception(e)
            self.is_playing = False
            self.stop_flag[0] = True


    def start_scenario(self, num):
        if self.is_playing:
            return
        self.current_play_scenario = num
        self.is_playing = True
        self.stop_flag[0] = False
        self.start_scenario_in_thread(num)

    def play_complete_callback(self):
        onboard_led.turn_off()
        print("Onboard LED: OFF (Scenario completed)")
        self.is_playing = False
        self.stop_flag[0] = False
        print("再生が終了しました。")

        if self.select_mode:
            self.update_oled_select_mode_display()
        else:
            if self.current_display != self.push_message:
                self.dm.push_message([self.push_message])
                self.current_display = self.push_message

    # ----------------------------------------------------------------------
    # ボタン処理
    # ----------------------------------------------------------------------
    def handle_button(self, button):
        now = time.ticks_ms()
        current_state = button.value()  # 押下:1, 離:0 の想定

        # 押下開始
        if current_state == 1 and not self.button_pressed:
            self.button_pressed = True
            self.press_time = now
            self.last_press_time = now
            self.last_user_interaction_time = now

        # 長押し検出（通常モード → セレクトモード）
        elif current_state == 1 and self.button_pressed:
            if time.ticks_diff(now, self.press_time) >= self.BUTTON_LONG_PRESS_MS and not self.select_mode and not self.is_playing:
                self.select_mode = True
                print("=== Select Mode Start ===")
                self.update_oled_select_mode_display()
                self.last_user_interaction_time = now

        # 離した瞬間
        elif current_state == 0 and self.button_pressed:
            self.button_pressed = False
            self.release_time = now
            press_duration = time.ticks_diff(now, self.press_time)
            self.last_user_interaction_time = now

            if self.select_mode:
                # セレクトモード内の短押し・長押し判定
                if press_duration < self.BUTTON_SHORT_PRESS_MS:
                    self.click_count += 1
                    self.last_click_time = now
                elif press_duration >= self.BUTTON_LONG_PRESS_MS:
                    scenario = self.valid_scenarios[self.selected_index]
                    print(f"Play Scenario: {scenario}")
                    self.start_scenario(scenario)
            else:
                # 通常モードの短押しによるランダム再生
                if press_duration < self.BUTTON_SHORT_PRESS_MS and not self.is_playing and self.random_scenarios:
                    scenario = random.choice(self.random_scenarios)
                    print(f"Random Play Scenario: {scenario}")
                    self.start_scenario(scenario)
                elif self.is_playing:
                    print("Playback stopped by user.")
                    self.stop_flag[0] = True
                    self.is_playing = False
                    onboard_led.turn_off()
                    self.dm.push_message(["Stopped"])

        # セレクトモード内の選択更新（短押し連打）
        if self.select_mode and self.click_count > 0:
            if time.ticks_diff(now, self.last_click_time) > self.BUTTON_DOUBLE_CLICK_INTERVAL_MS:
                num_scenarios = len(self.valid_scenarios)
                if self.click_count == 1:
                    self.selected_index = (self.selected_index + 1) % num_scenarios
                elif self.click_count == 2:
                    self.selected_index = (self.selected_index - 1 + num_scenarios) % num_scenarios
                else:
                    self.selected_index = (self.selected_index + 1) % num_scenarios
                self.selected_scenario = self.valid_scenarios[self.selected_index]
                print(f"Selected Scenario: {self.selected_scenario}")
                self.update_oled_select_mode_display()
                self.click_count = 0

    # ----------------------------------------------------------------------
    # アイドル監視＆自動再生
    # ----------------------------------------------------------------------
    def check_idle_autoplay(self):
        now = time.ticks_ms()
        if self.is_playing or self.select_mode or not self.random_scenarios:
            return
        idle_elapsed = time.ticks_diff(now, self.last_user_interaction_time)
        auto_elapsed = time.ticks_diff(now, self.last_auto_play_time)

        if idle_elapsed >= self.IDLE_TIMEOUT_MS and auto_elapsed >= self.AUTO_PLAY_INTERVAL_MS:
            scenario = random.choice(self.random_scenarios)
            print(f"[AutoPlay] Scenario: {scenario}")
            self.last_auto_play_time = now
            self.start_scenario(scenario)

    def update_playback(self):
        """
        再生中の処理。メインループから定期的に呼び出すことを想定。
        - self.current_play_scenario にシナリオキーがセットされていれば effects.playEffectByNum を実行
        - 再生終了後は play_complete_callback() を呼ぶ
        注意：effects.playEffectByNum はブロッキングで完了する前提の処理なので、
              別スレッドで起動する設計に戻す場合は競合に注意。
        """
        # 再生フラグ・対象がなければ何もしない
        if not self.is_playing or self.current_play_scenario is None:
            return

        # 実際の効果再生（blocks until finished or stop_flag observed）
        try:
            effects.playEffectByNum(self.scenarios_data, self.current_play_scenario, self.stop_flag)
        except OSError as e:
            # ハードウェア関連エラー
            print(f"[Hardware Error] Playback failed for scenario {self.current_play_scenario}: {e}")
            self.dm.push_message(["Hardware", "Error"])
        except KeyError as e:
            # シナリオキーが存在しない
            print(f"[Data Error] Invalid scenario {self.current_play_scenario}: {e}")
            self.dm.push_message(["Invalid", "Scenario"])
        except ValueError as e:
            # データ形式エラー
            print(f"[Data Error] Invalid data in scenario {self.current_play_scenario}: {e}")
            self.dm.push_message(["Data", "Error"])
        except Exception as e:
            # 再生中に例外が出ても状態を整えておく
            print(f"[Error] effects.playEffectByNum failed: {e}")
            import sys
            sys.print_exception(e)
            self.dm.push_message(["Playback", "Error"])
        finally:
            # 再生完了処理
            try:
                self.play_complete_callback()
            except Exception as e:
                print(f"[Critical Error] play_complete_callback failed: {e}")
                import sys
                sys.print_exception(e)
            # 再生対象をクリア
            self.current_play_scenario = None
