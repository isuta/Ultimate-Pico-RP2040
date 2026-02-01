"""logger.py

軽量なログ出力ユーティリティ

MicroPython環境向けに最適化されたシンプルなログ機能を提供します。
config.pyのLOG_LEVELに基づいてログ出力を制御します。

ログレベル:
- DEBUG (3): 詳細な動作情報、変数の値など
- INFO (2): 通常の動作状況、成功メッセージ
- WARNING (1): 問題だが動作継続可能な警告
- ERROR (0): 重大な問題、機能不全
"""

import config

# ログレベル定義
LOG_LEVELS = {
    'ERROR': 0,
    'WARNING': 1,
    'INFO': 2,
    'DEBUG': 3
}

def _should_log(level):
    """
    指定されたログレベルが出力対象かチェック
    
    Args:
        level: ログレベル文字列 ('ERROR', 'WARNING', 'INFO', 'DEBUG')
    
    Returns:
        bool: 出力すべき場合True
    """
    current_level = getattr(config, 'LOG_LEVEL', 2)
    return LOG_LEVELS.get(level, 0) <= current_level

def log_debug(msg):
    """
    デバッグメッセージを出力（LOG_LEVEL >= 3）
    
    用途: 詳細な動作情報、変数の値、内部状態
    例: "サーボ#0を速度50で回転開始", "ADC値: 32768"
    
    Args:
        msg: ログメッセージ
    """
    if _should_log('DEBUG'):
        print(f"[DEBUG] {msg}")

def log_info(msg):
    """
    情報メッセージを出力（LOG_LEVEL >= 2）
    
    用途: 通常の動作状況、成功メッセージ、システム状態
    例: "シナリオ再生完了", "Button: OK", "OLED: 初期化成功"
    
    Args:
        msg: ログメッセージ
    """
    if _should_log('INFO'):
        print(f"[INFO] {msg}")

def log_warning(msg):
    """
    警告メッセージを出力（LOG_LEVEL >= 1）
    
    用途: 問題だが動作継続可能、スキップ処理、フォールバック
    例: "DFPlayer利用不可（スキップ）", "Volume pot OK, DFPlayer missing"
    
    Args:
        msg: ログメッセージ
    """
    if _should_log('WARNING'):
        print(f"[WARN] {msg}")

def log_error(msg):
    """
    エラーメッセージを出力（常に表示）
    
    用途: 重大な問題、機能不全、例外発生
    例: "Thread start failed", "Memory Error", "JSON parse error"
    
    Args:
        msg: ログメッセージ
    """
    if _should_log('ERROR'):
        print(f"[ERROR] {msg}")

def log(level, msg):
    """
    汎用ログ出力関数
    
    Args:
        level: ログレベル ('error', 'warning', 'info', 'debug')
        msg: ログメッセージ
    """
    level_upper = level.upper()
    if level_upper == 'ERROR':
        log_error(msg)
    elif level_upper == 'WARNING':
        log_warning(msg)
    elif level_upper == 'INFO':
        log_info(msg)
    elif level_upper == 'DEBUG':
        log_debug(msg)
    else:
        # 不明なレベルはINFOとして扱う
        log_info(msg)
