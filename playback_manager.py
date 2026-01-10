# playback_manager.py
import time
import gc
import effects
import _thread
import logger

class PlaybackManager:
    """シナリオ再生管理を担当するクラス"""

    def __init__(self, scenarios_data, config=None):
        self.scenarios_data = scenarios_data
        self.is_playing = False
        self.stop_flag = [False]
        self.current_play_scenario = None
        self.play_complete_callback = None
        
        # メモリ管理設定
        self.gc_on_complete = getattr(config, 'GC_ON_SCENARIO_COMPLETE', True) if config else True
        self.gc_memory_logging = getattr(config, 'GC_MEMORY_LOGGING', False) if config else False

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
            logger.log_info("Scenario already playing — ignoring request")
            return
        
        self.current_play_scenario = num
        self.is_playing = True
        self.stop_flag[0] = False
        self._start_scenario_in_thread(num, dm)

    def _start_scenario_in_thread(self, num, dm):
        """スレッドで再生（起動失敗を安全にハンドル）"""
        def thread_func():
            try:
                # シナリオデータを取得
                if num not in self.scenarios_data:
                    raise KeyError(f"Scenario '{num}' not found")
                
                scenario_commands = self.scenarios_data[num]
                effects.execute_command(scenario_commands, self.stop_flag)
            except OSError as e:
                # ハードウェア関連エラー（GPIO, I2C, UART等）
                logger.log_error(f"Scenario {num} failed: {e}")
                dm.push_message(["Hardware", "Error"])
            except KeyError as e:
                # シナリオデータの不整合
                logger.log_error(f"Invalid scenario key {num}: {e}")
                dm.push_message(["Invalid", "Scenario"])
            except MemoryError as e:
                # メモリ不足
                logger.log_error(f"Out of memory in scenario {num}: {e}")
                dm.push_message(["Memory", "Error"])
            except Exception as e:
                # その他の予期しないエラー
                logger.log_error(f"Scenario thread failed: {e}")
                import sys
                sys.print_exception(e)
                dm.push_message(["Playback", "Error"])
            finally:
                # 再生終了処理（例外時でも呼ぶ）
                try:
                    self._on_play_complete()
                except Exception as e2:
                    logger.log_error(f"play_complete_callback failed: {e2}")
                    import sys
                    sys.print_exception(e2)

        # スレッド起動を試行
        try:
            _thread.start_new_thread(thread_func, ())
        except OSError as e:
            # スレッド起動失敗（core1 in use, メモリ不足など）
            logger.log_error(f"Thread start failed: {e}")
            dm.push_message(["Thread", "Error"])
            self.is_playing = False
            self.stop_flag[0] = True
        except RuntimeError as e:
            # ランタイムエラー
            logger.log_error(f"Thread creation failed: {e}")
            dm.push_message(["System", "Error"])
            self.is_playing = False
            self.stop_flag[0] = True
        except Exception as e:
            logger.log_error(f"Thread start error: {e}")
            import sys
            sys.print_exception(e)
            self.is_playing = False
            self.stop_flag[0] = True

    def stop_playback(self, dm):
        """再生を停止"""
        if not self.is_playing:
            return
        
        logger.log_info("Playback stopped by user.")
        self.stop_flag[0] = True
        self.is_playing = False
        dm.push_message(["Stopped"])

    def _on_play_complete(self):
        """再生完了時の内部処理"""
        self.is_playing = False
        self.stop_flag[0] = False
        self.current_play_scenario = None
        
        # シナリオ完了時のガーベージコレクション
        if self.gc_on_complete:
            try:
                if self.gc_memory_logging:
                    try:
                        mem_free_before = gc.mem_free()
                        mem_alloc_before = gc.mem_alloc()
                        logger.log_debug(f"Before scenario GC - Free: {mem_free_before}, Allocated: {mem_alloc_before}")
                    except Exception:
                        pass
                
                gc.collect()
                
                if self.gc_memory_logging:
                    try:
                        mem_free_after = gc.mem_free()
                        mem_alloc_after = gc.mem_alloc()
                        freed = mem_free_after - mem_free_before
                        logger.log_debug(f"After scenario GC  - Free: {mem_free_after}, Allocated: {mem_alloc_after}, Freed: {freed}")
                    except Exception:
                        pass
            except Exception as e:
                logger.log_warning(f"Scenario completion GC failed: {e}")
        
        # 外部コールバック呼び出し
        if self.play_complete_callback:
            self.play_complete_callback()

    def is_busy(self):
        """再生中かどうかを返す"""
        return self.is_playing
