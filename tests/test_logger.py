"""
Test suite for logger.py

PC上で実行可能な単体テスト
実行方法: python tests/test_logger.py
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# テスト用のダミーconfig
class DummyConfig:
    LOG_LEVEL = 2

# configモジュールを差し替え
sys.modules['config'] = DummyConfig()
import config

from logger import _should_log, LOG_LEVELS

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

# ===== _should_log のテスト =====
def test_should_log_level_0():
    """LOG_LEVEL=0（ERRORのみ）のテスト"""
    print("\n=== LOG_LEVEL=0（ERRORのみ）===")
    config.LOG_LEVEL = 0
    
    assert_equal(_should_log('ERROR'), True, "ERROR（レベル0）は表示")
    assert_equal(_should_log('WARNING'), False, "WARNING（レベル1）は非表示")
    assert_equal(_should_log('INFO'), False, "INFO（レベル2）は非表示")
    assert_equal(_should_log('DEBUG'), False, "DEBUG（レベル3）は非表示")

def test_should_log_level_1():
    """LOG_LEVEL=1（ERROR+WARNING）のテスト"""
    print("\n=== LOG_LEVEL=1（ERROR+WARNING）===")
    config.LOG_LEVEL = 1
    
    assert_equal(_should_log('ERROR'), True, "ERROR（レベル0）は表示")
    assert_equal(_should_log('WARNING'), True, "WARNING（レベル1）は表示")
    assert_equal(_should_log('INFO'), False, "INFO（レベル2）は非表示")
    assert_equal(_should_log('DEBUG'), False, "DEBUG（レベル3）は非表示")

def test_should_log_level_2():
    """LOG_LEVEL=2（ERROR+WARNING+INFO）のテスト - デフォルト"""
    print("\n=== LOG_LEVEL=2（ERROR+WARNING+INFO）- デフォルト ===")
    config.LOG_LEVEL = 2
    
    assert_equal(_should_log('ERROR'), True, "ERROR（レベル0）は表示")
    assert_equal(_should_log('WARNING'), True, "WARNING（レベル1）は表示")
    assert_equal(_should_log('INFO'), True, "INFO（レベル2）は表示")
    assert_equal(_should_log('DEBUG'), False, "DEBUG（レベル3）は非表示")

def test_should_log_level_3():
    """LOG_LEVEL=3（すべて表示）のテスト"""
    print("\n=== LOG_LEVEL=3（すべて表示）===")
    config.LOG_LEVEL = 3
    
    assert_equal(_should_log('ERROR'), True, "ERROR（レベル0）は表示")
    assert_equal(_should_log('WARNING'), True, "WARNING（レベル1）は表示")
    assert_equal(_should_log('INFO'), True, "INFO（レベル2）は表示")
    assert_equal(_should_log('DEBUG'), True, "DEBUG（レベル3）は表示")

def test_should_log_undefined():
    """LOG_LEVELが未定義の場合のテスト"""
    print("\n=== LOG_LEVEL未定義（デフォルト2）===")
    if hasattr(config, 'LOG_LEVEL'):
        delattr(config, 'LOG_LEVEL')
    
    # getattr(config, 'LOG_LEVEL', 2) でデフォルト2が使われる
    assert_equal(_should_log('ERROR'), True, "ERROR（レベル0）は表示")
    assert_equal(_should_log('WARNING'), True, "WARNING（レベル1）は表示")
    assert_equal(_should_log('INFO'), True, "INFO（レベル2）は表示")
    assert_equal(_should_log('DEBUG'), False, "DEBUG（レベル3）は非表示")
    
    # 元に戻す
    config.LOG_LEVEL = 2

# ===== すべてのテストを実行 =====
def run_all_tests():
    print("=" * 60)
    print("Logger テストスイート")
    print("=" * 60)
    
    test_should_log_level_0()
    test_should_log_level_1()
    test_should_log_level_2()
    test_should_log_level_3()
    test_should_log_undefined()
    
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
