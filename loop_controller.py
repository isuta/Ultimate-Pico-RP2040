# loop_controller.py
"""
メインループの制御ロジックを管理するモジュール
各種ハードウェアの更新処理を統合し、エラーハンドリングを一元化
"""
import time


class LoopController:
    """メインループの制御を担当するクラス"""
    
    def __init__(self, state_manager, volume_controller, button, button_available, polling_delay_ms, onboard_led=None, config=None):
        """
        Args:
            state_manager: StateManagerのインスタンス
            volume_controller: PollingVolumeControllerのインスタンス
            button: ボタンのPinオブジェクト（Noneの場合はボタン無効）
            button_available: ボタンが利用可能かどうか
            polling_delay_ms: ポーリング間隔（ミリ秒）
            onboard_led: 内蔵LEDモジュール（オプション）
            config: 設定モジュール（オプション）
        """
        self.state = state_manager
        self.vc = volume_controller
        self.button = button
        self.button_available = button_available
        self.polling_delay_ms = polling_delay_ms
        self.onboard_led = onboard_led
        self.loop_counter = 0
        self.running = True
        
        # エラーリトライ設定
        self.error_retry_delay_ms = getattr(config, 'ERROR_RETRY_DELAY_MS', 1000) if config else 1000
    
    def update_volume(self, current_time):
        """ボリューム制御の更新"""
        try:
            self.vc.poll(current_time)
        except OSError as e:
            print(f"[Hardware Error] Volume poll error: {e}")
        except Exception as e:
            print(f"[Warning] Volume poll error: {e}")
    
    def update_button(self):
        """ボタン入力の処理"""
        if not self.button_available:
            return
        
        try:
            self.state.handle_button(self.button)
        except OSError as e:
            print(f"[Hardware Error] Button handling failed: {e}")
            import sys
            sys.print_exception(e)
        except Exception as e:
            print(f"[Error] Button handling failed: {e}")
            import sys
            sys.print_exception(e)
    
    def update_idle_autoplay(self):
        """アイドル状態の自動再生チェック"""
        try:
            self.state.check_idle_autoplay()
        except Exception as e:
            print(f"[Error] Idle autoplay check failed: {e}")
            import sys
            sys.print_exception(e)
    
    def update_playback(self):
        """再生処理の更新"""
        try:
            self.state.update_playback()
        except OSError as e:
            print(f"[Hardware Error] Playback update failed: {e}")
            import sys
            sys.print_exception(e)
        except Exception as e:
            print(f"[Error] Playback update failed: {e}")
            import sys
            sys.print_exception(e)
    
    def run_single_iteration(self):
        """メインループの1回分の処理を実行"""
        current_time = time.ticks_ms()
        
        # 各処理を順番に実行
        self.update_volume(current_time)
        self.update_button()
        self.update_idle_autoplay()
        self.update_playback()
        
        # ループウェイト
        time.sleep_ms(self.polling_delay_ms)
        self.loop_counter += 1
    
    def run(self):
        """メインループを実行"""
        try:
            while self.running:
                try:
                    self.run_single_iteration()
                except KeyboardInterrupt:
                    # Ctrl+C で停止
                    print("\n[Info] KeyboardInterrupt detected. Shutting down...")
                    self.running = False
                    break
                except Exception as e:
                    # メインループ内の予期しないエラー
                    print(f"[Critical Error] Main loop error: {e}")
                    import sys
                    sys.print_exception(e)
                    # エラーが発生してもループを継続（システムダウンを防ぐ）
                    time.sleep_ms(self.error_retry_delay_ms)  # エラー時の待機
        
        except Exception as e:
            # 最上位レベルのエラー
            print(f"[Fatal Error] System failure: {e}")
            import sys
            sys.print_exception(e)
        finally:
            # クリーンアップ処理
            self.cleanup()
    
    def cleanup(self):
        """システムのクリーンアップ処理"""
        print("\n[Info] System cleanup...")
        try:
            if self.onboard_led:
                self.onboard_led.turn_off()
        except Exception as e:
            print(f"[Warning] Cleanup error: {e}")
        print("[Info] System stopped.")
    
    def stop(self):
        """ループを停止"""
        self.running = False
