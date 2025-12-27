# sound_command_handler.py
# DFPlayer Miniサウンドコマンドのハンドラー

import sound_patterns
import command_parser

def handle(cmd, stop_flag_ref):
    """
    サウンドコマンドを処理します（辞書形式・リスト形式両対応）。
    
    Args:
        cmd: コマンド辞書またはリスト
        stop_flag_ref: 停止フラグのリスト参照 [bool]
    """
    if isinstance(cmd, dict):
        _handle_dict_format(cmd)
    elif isinstance(cmd, list):
        _handle_list_format(cmd)
    else:
        print(f"[Warning] Unknown sound command format: {cmd}")

def _handle_dict_format(cmd):
    """
    辞書形式のサウンドコマンドを処理します。
    
    Args:
        cmd: コマンド辞書 {"type": "sound", "folder": 2, "file": 1}
    """
    folder_num = command_parser.get_param(cmd, "folder")
    file_num = command_parser.get_param(cmd, "file")
    
    if folder_num is None or file_num is None:
        print(f"[Data Error] folder and file required for sound command")
        return
    
    _play_sound(folder_num, file_num)

def _handle_list_format(cmd):
    """
    リスト形式のサウンドコマンドを処理します。
    
    Args:
        cmd: コマンドリスト ["sound", folder_num, file_num]
    """
    if len(cmd) != 3:
        print(f"[Data Error] sound command requires 3 elements: {cmd}")
        return
    
    folder_num = cmd[1]
    file_num = cmd[2]
    
    _play_sound(folder_num, file_num)

def _play_sound(folder_num, file_num):
    """
    サウンドを再生します。
    
    Args:
        folder_num: フォルダ番号
        file_num: ファイル番号
    """
    if not sound_patterns.is_dfplayer_available():
        print(f"[Warning] Sound: フォルダ{folder_num}のファイル{file_num}を再生（スキップ - DFPlayer利用不可）")
        return
    
    command_parser.safe_call(
        sound_patterns.play_sound,
        folder_num, file_num,
        error_context=f"Sound play folder={folder_num}, file={file_num}"
    )
