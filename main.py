import time

# --- 各モジュールインポート ---
import sound_patterns
import effects
import onboard_led
import volume_control
import display_manager
import system_init       # 初期化モジュール
import state_manager     # 状態管理モジュール

# --- 初期化 ---
hw = system_init.initialize_system()

# dict から必要な情報を取り出す
button = hw["button"]
button_available = hw["button_available"]
volume_pot = hw["volume_pot"]
current_volume = hw["current_volume"]
LAST_VOLUME_READING = 0  # 初期値

IDLE_TIMEOUT_MS = hw["timeouts"]["idle"]
POLLING_DELAY_MS = hw["timeouts"]["polling"]
AUTO_PLAY_INTERVAL_MS = hw["timeouts"]["autoplay"]

dm = hw["display"]
vc = hw["volume_controller"]

scenarios_data = hw["scenarios"]
valid_scenarios = hw["valid_scenarios"]
random_scenarios = hw["random_scenarios"]

onboard_led = hw.get("onboard_led")

# --- 状態管理クラスのインスタンス化 ---
state = state_manager.StateManager(
    dm=dm,
    vc=vc,
    scenarios_data=scenarios_data,
    valid_scenarios=valid_scenarios,
    random_scenarios=random_scenarios,
    config=system_init.config
)

# --- effects初期化 ---
try:
    effects.init()
    print("Effects モジュール初期化完了")
except Exception as e:
    print(f"Effects 初期化中にエラー: {e}")

# --- メインループ ---
loop_counter = 0
adc_check_interval = max(1, int(100 / POLLING_DELAY_MS))

if not button_available:
    print("\n=== Console-Only Mode ===")
    print("Running in console-only mode due to button initialization failure.")
    print("System will automatically start random playback after idle timeout.")
    print(f"Idle timeout: {IDLE_TIMEOUT_MS/1000} seconds")
    print(f"Auto-play interval: {AUTO_PLAY_INTERVAL_MS/1000} seconds")
    print("=========================\n")

while True:
    current_time = time.ticks_ms()

    # ボリュームポーリング処理
    vc.poll(current_time)

    # ボタン入力処理
    if button_available:
        state.handle_button(button)

    # アイドル状態の自動再生チェック
    state.check_idle_autoplay()

    # 再生処理（スレッドを使わず安全に実行）
    state.update_playback()

    # ループウェイト
    time.sleep_ms(POLLING_DELAY_MS)
    loop_counter += 1

