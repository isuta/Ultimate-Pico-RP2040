# playback_manager.py
import time
import effects
import onboard_led
import _thread

class PlaybackManager:
    """シナリオ再生管理を担当するクラス"""

    def __init__(self, scenarios_data):
        self.scenarios_data = scenarios_data
        self.is_playing = False
        self.stop_flag = [False]
        self.current_play_scenario = None
        self.play_complete_callback = None

    def set_complete_callback(self, callback):
        """再生完了時のコールバックを設定"""
        self.play_complete_callback = callback

    def start_scenario(self, num, dm):
        """
        シナリオ再生を開始
        
        Args:
            num: シナリオ番号
            dm: DisplayManager インスタンス（エラー表示用）
        """
        if self.is_playing:
            print("[Debug] start_scenario: already playing — ignore")
            return
        
        self.current_play_scenario = num
        self.is_playing = True
        self.stop_flag[0] = False
        self._start_scenario_in_thread(num, dm)

    def _start_scenario_in_thread(self, num, dm):
        """スレッドで再生（起動失敗を安全にハンドル）"""
        def thread_func():
            try:
                onboard_led.turn_on()
                
                # シナリオデータを取得
                if num not in self.scenarios_data:
                    raise KeyError(f"Scenario '{num}' not found")
                
                scenario_commands = self.scenarios_data[num]
                effects.execute_command(scenario_commands, self.stop_flag)
            except OSError as e:
                # ハードウェア関連エラー（GPIO, I2C, UART等）
                print(f"[Hardware Error] Scenario {num} failed: {e}")
                dm.push_message(["Hardware", "Error"])
            except KeyError as e:
                # シナリオデータの不整合
                print(f"[Data Error] Invalid scenario key {num}: {e}")
                dm.push_message(["Invalid", "Scenario"])
            except MemoryError as e:
                # メモリ不足
                print(f"[Memory Error] Out of memory in scenario {num}: {e}")
                dm.push_message(["Memory", "Error"])
            except Exception as e:
                # その他の予期しないエラー
                print(f"[Error] Scenario thread failed: {e}")
                import sys
                sys.print_exception(e)
                dm.push_message(["Playback", "Error"])
            finally:
                # 再生終了処理（例外時でも呼ぶ）
                try:
                    self._on_play_complete()
                except Exception as e2:
                    print(f"[Critical Error] play_complete_callback failed: {e2}")
                    import sys
                    sys.print_exception(e2)

        # スレッド起動を試行
        try:
            _thread.start_new_thread(thread_func, ())
        except OSError as e:
            # スレッド起動失敗（core1 in use, メモリ不足など）
            print(f"[Thread Error] Thread start failed: {e}")
            dm.push_message(["Thread", "Error"])
            self.is_playing = False
            self.stop_flag[0] = True
        except RuntimeError as e:
            # ランタイムエラー
            print(f"[Runtime Error] Thread creation failed: {e}")
            dm.push_message(["System", "Error"])
            self.is_playing = False
            self.stop_flag[0] = True
        except Exception as e:
            print(f"[Unexpected Error] Thread start error: {e}")
            import sys
            sys.print_exception(e)
            self.is_playing = False
            self.stop_flag[0] = True

    def stop_playback(self, dm):
        """再生を停止"""
        if not self.is_playing:
            return
        
        print("Playback stopped by user.")
        self.stop_flag[0] = True
        self.is_playing = False
        onboard_led.turn_off()
        dm.push_message(["Stopped"])

    def _on_play_complete(self):
        """再生完了時の内部処理"""
        onboard_led.turn_off()
        self.is_playing = False
        self.stop_flag[0] = False
        self.current_play_scenario = None
        
        # 外部コールバック呼び出し
        if self.play_complete_callback:
            self.play_complete_callback()

    def is_busy(self):
        """再生中かどうかを返す"""
        return self.is_playing
