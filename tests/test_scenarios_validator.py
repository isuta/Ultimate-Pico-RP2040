"""
Scenarios JSON Validator

scenarios.jsonの形式と内容を検証するスクリプト
実行方法: python tests/test_scenarios_validator.py
"""

import json
import sys
from pathlib import Path

# テストカウンター
tests_passed = 0
tests_failed = 0
warnings = []

def log_pass(message):
    """成功ログ"""
    global tests_passed
    tests_passed += 1
    print(f"✓ {message}")

def log_fail(message):
    """失敗ログ"""
    global tests_failed
    tests_failed += 1
    print(f"✗ {message}")

def log_warning(message):
    """警告ログ"""
    warnings.append(message)
    print(f"⚠ {message}")

def validate_json_format(filepath):
    """JSONファイルの読み込みと基本形式チェック"""
    print("\n=== JSON形式の検証 ===")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        log_pass("JSONファイルの読み込み成功")
        return data
    except FileNotFoundError:
        log_fail(f"ファイルが見つかりません: {filepath}")
        return None
    except json.JSONDecodeError as e:
        log_fail(f"JSON形式エラー: {e}")
        return None
    except Exception as e:
        log_fail(f"予期しないエラー: {e}")
        return None

def validate_structure(data):
    """データ構造の検証"""
    print("\n=== データ構造の検証 ===")
    
    if not isinstance(data, dict):
        log_fail("トップレベルは辞書である必要があります")
        return False
    
    log_pass("トップレベルは辞書形式")
    
    if len(data) == 0:
        log_warning("シナリオが1つもありません")
        return True
    
    log_pass(f"{len(data)}個のシナリオを検出")
    return True

def validate_scenario_keys(data):
    """シナリオキーの検証"""
    print("\n=== シナリオキーの検証 ===")
    
    for key in data.keys():
        try:
            scenario_num = int(key)
            if scenario_num < 0:
                log_warning(f"シナリオ番号が負数です: {key}")
            else:
                log_pass(f"シナリオ {key}: 数値キー（ランダム再生対象）")
        except ValueError:
            # 文字列キーは仕様として許容（テスト用シナリオ等で使用）
            log_pass(f"シナリオ {key}: 文字列キー（手動選択のみ）")

def validate_scenario_content(data):
    """各シナリオの内容検証"""
    print("\n=== シナリオ内容の検証 ===")
    
    for key, scenario in data.items():
        # シナリオはリストである必要がある
        if not isinstance(scenario, list):
            log_fail(f"シナリオ {key}: コマンドリストではありません（{type(scenario).__name__}）")
            continue
        
        log_pass(f"シナリオ {key}: {len(scenario)}個のコマンド")
        
        # 各コマンドの検証
        for idx, cmd in enumerate(scenario):
            validate_command(key, idx, cmd)

def validate_command(scenario_key, cmd_idx, cmd):
    """個別コマンドの検証"""
    
    # コマンドは辞書またはリスト
    if not isinstance(cmd, (dict, list)):
        log_fail(f"シナリオ {scenario_key}[{cmd_idx}]: コマンド形式が不正（{type(cmd).__name__}）")
        return
    
    # リスト形式の場合
    if isinstance(cmd, list):
        if len(cmd) == 0:
            log_warning(f"シナリオ {scenario_key}[{cmd_idx}]: 空のコマンド")
            return
        
        cmd_type = cmd[0]
        
        # delayコマンドのチェック
        if cmd_type == "delay":
            if len(cmd) < 2:
                log_fail(f"シナリオ {scenario_key}[{cmd_idx}]: delayコマンドに時間が指定されていません")
            elif not isinstance(cmd[1], (int, float)) or cmd[1] < 0:
                log_fail(f"シナリオ {scenario_key}[{cmd_idx}]: delay時間が不正です（{cmd[1]}）")
    
    # 辞書形式の場合
    elif isinstance(cmd, dict):
        if len(cmd) == 0:
            log_warning(f"シナリオ {scenario_key}[{cmd_idx}]: 空のコマンド辞書")
            return
        
        # 基本的なキーの存在チェック
        if "type" in cmd:
            cmd_type = cmd["type"]
        else:
            cmd_type = next(iter(cmd.keys()))

def validate_common_issues(data):
    """よくある問題のチェック"""
    print("\n=== よくある問題のチェック ===")
    
    for key, scenario in data.items():
        if not isinstance(scenario, list):
            continue
        
        # 1. 最後のカンマ
        # (JSONパーサーがエラーを出すのでここまで来れば問題なし)
        
        # 2. delayが0のコマンド
        for idx, cmd in enumerate(scenario):
            if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "delay" and cmd[1] == 0:
                log_warning(f"シナリオ {key}[{idx}]: delay 0 は意味がありません")
        
        # 3. 非常に長いシナリオ
        if len(scenario) > 100:
            log_warning(f"シナリオ {key}: コマンド数が多すぎます（{len(scenario)}個、メモリ不足の可能性）")

def run_validation(filepath):
    """すべての検証を実行"""
    print("=" * 60)
    print(f"Scenarios JSON バリデーター")
    print(f"対象ファイル: {filepath}")
    print("=" * 60)
    
    # JSON読み込み
    data = validate_json_format(filepath)
    if data is None:
        return 1
    
    # 構造検証
    if not validate_structure(data):
        return 1
    
    # キー検証
    validate_scenario_keys(data)
    
    # 内容検証
    validate_scenario_content(data)
    
    # よくある問題チェック
    validate_common_issues(data)
    
    # 結果表示
    print("\n" + "=" * 60)
    print(f"検証結果: {tests_passed} 合格 / {tests_failed} 失敗 / {len(warnings)} 警告")
    print("=" * 60)
    
    if tests_failed == 0:
        print("✅ 致命的なエラーはありません")
        if len(warnings) > 0:
            print(f"⚠️  {len(warnings)}件の警告があります（動作には影響しません）")
        return 0
    else:
        print(f"❌ {tests_failed}件の致命的なエラーがあります")
        return 1

if __name__ == "__main__":
    # scenarios.jsonのパスを取得
    script_dir = Path(__file__).parent
    scenarios_path = script_dir.parent / "scenarios.json"
    
    exit_code = run_validation(scenarios_path)
    sys.exit(exit_code)
