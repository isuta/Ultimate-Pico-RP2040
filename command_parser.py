# command_parser.py
# JSON解析・パラメータ抽出・バリデーションの共通処理

import time

def get_param(cmd, key, default=None):
    """
    辞書から安全にパラメータを取得します。
    
    Args:
        cmd: コマンド辞書
        key: 取得するキー
        default: デフォルト値
    
    Returns:
        パラメータ値（存在しない場合はdefault）
    """
    return cmd.get(key, default)

def validate_range(value, min_val, max_val, name):
    """
    値が範囲内にあるかチェックし、範囲外の場合はクランプします。
    
    Args:
        value: チェックする値
        min_val: 最小値
        max_val: 最大値
        name: パラメータ名（ログ用）
    
    Returns:
        範囲内にクランプされた値
    """
    if not min_val <= value <= max_val:
        print(f"[Warning] {name} {value} out of range ({min_val}～{max_val}), clamping.")
        return max(min_val, min(max_val, value))
    return value

def validate_positive(value, name):
    """
    値が正数かチェックします。
    
    Args:
        value: チェックする値
        name: パラメータ名（ログ用）
    
    Returns:
        正数の場合True、それ以外False
    """
    if value < 0:
        print(f"[Warning] {name} {value} is negative, ignoring.")
        return False
    return True

def check_stop_flag(stop_flag_ref):
    """
    停止フラグをチェックします。
    
    Args:
        stop_flag_ref: 停止フラグのリスト参照 [bool]
    
    Returns:
        停止フラグがTrueの場合True
    """
    if stop_flag_ref and stop_flag_ref[0]:
        return True
    return False

def wait_with_stop_check(duration_ms, stop_flag_ref, check_interval_ms=50):
    """
    停止フラグを監視しながら指定時間待機します。
    
    Args:
        duration_ms: 待機時間（ミリ秒）
        stop_flag_ref: 停止フラグのリスト参照 [bool]
        check_interval_ms: フラグチェック間隔（ミリ秒）
    
    Returns:
        正常完了した場合True、中断された場合False
    """
    if duration_ms <= 0:
        return True
    
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
        if check_stop_flag(stop_flag_ref):
            print("[Info] Wait interrupted by stop_flag")
            return False
        time.sleep_ms(check_interval_ms)
    
    return True

def safe_call(func, *args, error_context="", **kwargs):
    """
    エラーハンドリング付きで関数を呼び出します。
    
    Args:
        func: 呼び出す関数
        *args: 関数の引数
        error_context: エラーメッセージ用のコンテキスト
        **kwargs: 関数のキーワード引数
    
    Returns:
        関数の戻り値（エラーの場合None）
    """
    try:
        return func(*args, **kwargs)
    except OSError as e:
        print(f"[Hardware Error] {error_context}: {e}")
        return None
    except Exception as e:
        print(f"[Error] {error_context}: {e}")
        import sys
        sys.print_exception(e)
        return None

def validate_color(color):
    """
    カラー値（RGB）をバリデーションします。
    
    Args:
        color: カラー値 [R, G, B] または (R, G, B)
    
    Returns:
        有効な場合 (R, G, B)、無効な場合None
    """
    if not (isinstance(color, (list, tuple)) and len(color) == 3):
        print(f"[Data Error] Invalid color format: {color}")
        return None
    
    r, g, b = color
    if not all(0 <= c <= 255 for c in [r, g, b]):
        print(f"[Data Error] Color values out of range: ({r}, {g}, {b})")
        return None
    
    return (int(r), int(g), int(b))

def parse_command_type(cmd):
    """
    コマンド辞書からコマンドタイプを取得します。
    
    Args:
        cmd: コマンド辞書または配列
    
    Returns:
        コマンドタイプ文字列、または None
    """
    if isinstance(cmd, dict):
        # "type" キーがあれば使用、なければ最初のキーをコマンドタイプとする
        if "type" in cmd:
            return cmd["type"]
        else:
            # led_on, led_off, led_fade_in 等
            return next(iter(cmd.keys())) if cmd else None
    elif isinstance(cmd, list) and cmd:
        return cmd[0]
    else:
        return None
