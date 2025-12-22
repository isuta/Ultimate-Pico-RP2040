# fade_controller.py
# 共通フェード処理モジュール
# PWM LEDとNeoPixelの両方で使用される汎用フェード処理を提供します

import time
import config

def linear_fade(start_value, end_value, duration_ms, step_interval_ms, update_callback, stop_flag_ref=None):
    """
    汎用線形フェード処理
    
    Args:
        start_value: 開始値（数値またはタプル/リスト）
        end_value: 終了値（数値またはタプル/リスト）
        duration_ms: フェード時間（ミリ秒）
        step_interval_ms: 更新間隔（ミリ秒）
        update_callback: 値を更新するためのコールバック関数 update_callback(current_value)
        stop_flag_ref: 停止フラグのリスト参照 [bool]（オプション）
    
    Returns:
        正常完了した場合True、中断/エラーの場合False
    """
    if duration_ms <= 0:
        # 時間が0以下の場合は即座に終了値を設定
        try:
            update_callback(end_value)
            return True
        except Exception as e:
            print(f"[Error] Fade immediate update failed: {e}")
            return False
    
    # 開始値と終了値が同じ場合は処理不要
    if start_value == end_value:
        return True
    
    # 値が単一の数値かタプル/リストかを判定
    is_tuple = isinstance(start_value, (tuple, list))
    
    if is_tuple:
        # タプル/リストの場合（RGB色など）
        if len(start_value) != len(end_value):
            print(f"[Error] Start and end value dimensions mismatch")
            return False
        
        # 各要素の変化量を計算
        start_values = [float(v) for v in start_value]
        delta_values = [float(end_value[i] - start_value[i]) for i in range(len(start_value))]
    else:
        # 単一数値の場合
        start_values = float(start_value)
        delta_values = float(end_value - start_value)
    
    # フェードパラメータの計算
    total_steps = max(1, duration_ms // step_interval_ms)
    start_time = time.ticks_ms()
    
    try:
        for step in range(total_steps + 1):
            # 停止フラグチェック
            if stop_flag_ref and stop_flag_ref[0]:
                print(f"[Info] Fade interrupted by stop_flag")
                return False
            
            # 経過時間から進捗率を計算
            elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
            if elapsed_ms >= duration_ms:
                # 最終ステップ：正確に目標値に設定
                update_callback(end_value)
                break
            
            # 進捗率（0.0～1.0）
            progress = elapsed_ms / duration_ms
            
            # 現在の値を計算
            if is_tuple:
                current_values = []
                for i in range(len(start_values)):
                    current = start_values[i] + (delta_values[i] * progress)
                    # 整数に変換してクリップ（0-255想定）
                    current = max(0, min(255, int(current)))
                    current_values.append(current)
                update_callback(current_values)
            else:
                current = start_values + (delta_values * progress)
                update_callback(current)
            
            # 次のステップまで待機
            time.sleep_ms(step_interval_ms)
        
        return True
        
    except Exception as e:
        print(f"[Error] Fade processing error: {e}")
        import sys
        sys.print_exception(e)
        return False


def wait_with_cancel(duration_ms, check_interval_ms, stop_flag_ref=None):
    """
    キャンセル可能な待機処理
    
    Args:
        duration_ms: 待機時間（ミリ秒）
        check_interval_ms: 停止フラグチェック間隔（ミリ秒）
        stop_flag_ref: 停止フラグのリスト参照 [bool]（オプション）
    
    Returns:
        正常完了した場合True、中断の場合False
    """
    if duration_ms <= 0:
        return True
    
    start_time = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
        if stop_flag_ref and stop_flag_ref[0]:
            print(f"[Info] Wait interrupted by stop_flag")
            return False
        time.sleep_ms(check_interval_ms)
    
    return True
