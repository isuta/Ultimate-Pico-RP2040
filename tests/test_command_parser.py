"""
Test suite for command_parser.py

PC上で実行可能な単体テスト
実行方法: python tests/test_command_parser.py
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from command_parser import (
    get_param,
    validate_range,
    validate_positive,
    validate_color,
    parse_command_type
)

# テストカウンター
tests_passed = 0
tests_failed = 0

def assert_equal(actual, expected, test_name):
    """テストアサーション"""
    global tests_passed, tests_failed
    if actual == expected:
        tests_passed += 1
        print(f"✓ {test_name}")
    else:
        tests_failed += 1
        print(f"✗ {test_name}")
        print(f"  Expected: {expected}")
        print(f"  Actual: {actual}")

# ===== get_param のテスト =====
def test_get_param():
    print("\n=== get_param() テスト ===")
    
    cmd = {"led": "on", "brightness": 100}
    
    # 正常取得
    assert_equal(get_param(cmd, "led"), "on", "存在するキーの取得")
    assert_equal(get_param(cmd, "brightness"), 100, "数値パラメータの取得")
    
    # デフォルト値
    assert_equal(get_param(cmd, "missing"), None, "存在しないキー（デフォルトNone）")
    assert_equal(get_param(cmd, "missing", 50), 50, "存在しないキー（デフォルト50）")
    
    # 空辞書
    assert_equal(get_param({}, "key", "default"), "default", "空辞書でデフォルト値")

# ===== validate_range のテスト =====
def test_validate_range():
    print("\n=== validate_range() テスト ===")
    
    # 範囲内
    assert_equal(validate_range(50, 0, 100, "value"), 50, "範囲内の値（中央）")
    assert_equal(validate_range(0, 0, 100, "value"), 0, "範囲内の値（最小）")
    assert_equal(validate_range(100, 0, 100, "value"), 100, "範囲内の値（最大）")
    
    # 範囲外（クランプ）
    assert_equal(validate_range(-10, 0, 100, "value"), 0, "範囲外（下限未満→クランプ）")
    assert_equal(validate_range(150, 0, 100, "value"), 100, "範囲外（上限超過→クランプ）")
    
    # 負の範囲
    assert_equal(validate_range(-50, -100, 100, "value"), -50, "負の範囲内")
    assert_equal(validate_range(-150, -100, 100, "value"), -100, "負の範囲外（クランプ）")

# ===== validate_positive のテスト =====
def test_validate_positive():
    print("\n=== validate_positive() テスト ===")
    
    # 正数
    assert_equal(validate_positive(1, "value"), True, "正数（1）")
    assert_equal(validate_positive(100, "value"), True, "正数（100）")
    assert_equal(validate_positive(0, "value"), True, "ゼロ（正数扱い）")
    
    # 負数
    assert_equal(validate_positive(-1, "value"), False, "負数（-1）")
    assert_equal(validate_positive(-100, "value"), False, "負数（-100）")

# ===== validate_color のテスト =====
def test_validate_color():
    print("\n=== validate_color() テスト ===")
    
    # 正常なカラー値
    assert_equal(validate_color([255, 128, 0]), (255, 128, 0), "リスト形式のRGB")
    assert_equal(validate_color((255, 128, 0)), (255, 128, 0), "タプル形式のRGB")
    assert_equal(validate_color([0, 0, 0]), (0, 0, 0), "黒（0,0,0）")
    assert_equal(validate_color([255, 255, 255]), (255, 255, 255), "白（255,255,255）")
    
    # 不正な形式
    assert_equal(validate_color([255, 128]), None, "要素数不足（2要素）")
    assert_equal(validate_color([255, 128, 0, 64]), None, "要素数過多（4要素）")
    assert_equal(validate_color("red"), None, "文字列")
    assert_equal(validate_color(None), None, "None")
    
    # 範囲外の値
    assert_equal(validate_color([256, 128, 0]), None, "R値が範囲外（256）")
    assert_equal(validate_color([255, -1, 0]), None, "G値が負数（-1）")
    assert_equal(validate_color([255, 128, 300]), None, "B値が範囲外（300）")

# ===== parse_command_type のテスト =====
def test_parse_command_type():
    print("\n=== parse_command_type() テスト ===")
    
    # 辞書形式（typeキー指定）
    assert_equal(parse_command_type({"type": "led", "command": "on"}), "led", "辞書形式（typeキー）")
    
    # 辞書形式（typeキーなし）
    assert_equal(parse_command_type({"led_on": {"brightness": 100}}), "led_on", "辞書形式（最初のキー）")
    
    # リスト形式
    assert_equal(parse_command_type(["delay", 1000]), "delay", "リスト形式")
    assert_equal(parse_command_type(["led", "on"]), "led", "リスト形式（複数要素）")
    
    # エッジケース
    assert_equal(parse_command_type([]), None, "空リスト")
    assert_equal(parse_command_type({}), None, "空辞書")
    assert_equal(parse_command_type(None), None, "None")
    assert_equal(parse_command_type("string"), None, "文字列")

# ===== すべてのテストを実行 =====
def run_all_tests():
    print("=" * 60)
    print("Command Parser テストスイート")
    print("=" * 60)
    
    test_get_param()
    test_validate_range()
    test_validate_positive()
    test_validate_color()
    test_parse_command_type()
    
    print("\n" + "=" * 60)
    print(f"テスト結果: {tests_passed} 合格 / {tests_failed} 失敗")
    print("=" * 60)
    
    if tests_failed == 0:
        print("✅ すべてのテストが合格しました！")
        return 0
    else:
        print(f"❌ {tests_failed}件のテストが失敗しました")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
