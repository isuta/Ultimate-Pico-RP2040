# =================================================================
# ハードウェア設定ファイル
# -----------------------------------------------------------------
# このファイルでは、Raspberry Pi Pico 2Wに接続された各種
# ハードウェアコンポーネントの設定を定義します。
# 
# 主要コンポーネント:
# - DFPlayer Mini (音声再生モジュール)
# - OLEDディスプレイ (SSD1306)
# - NeoPixel LEDストリップ x4
# - ステッピングモーター
# - タクトスイッチ (ユーザー入力)
# - ポテンショメータ (ボリューム調整)
#
# 設定変更時の注意事項:
# - GPIO番号を変更する場合は、物理的な配線も変更してください
# - I2CやUARTのピン番号は各ペリフェラルの制約に従ってください
# - NeoPixelのLED数は実際の接続数に合わせて調整してください
# - タイミング設定は実機で動作確認しながら調整することを推奨
# =================================================================

# UART設定
UART_ID = 0
UART_BAUDRATE = 9600
# DFPlayer Miniの接続ピン設定
DFPLAYER_TX_PIN = 12
DFPLAYER_RX_PIN = 13
DFPLAYER_BUSY_PIN = 14
DFPLAYER_DEFAULT_VOLUME = 5  # デフォルト音量

# I2C (OLEDディスプレイ用)
I2C_ID = 0
OLED_SDA_PIN = 16
OLED_SCL_PIN = 17
I2C_FREQ = 400000

# OLEDのサイズ設定
OLED_WIDTH = 128
OLED_HEIGHT = 64

# ボタン設定
BUTTON_PIN = 18

# 内蔵LED設定(Raspberry Pi Pico 2W)
ONBOARD_LED_PIN = "LED"  # 内蔵LEDへのアクセス識別子

# NeoPixel設定
# 論理名とピン番号・LED数を紐づけ
NEOPIXEL_STRIPS = {
    # 'ストリップ名': {'pin': ピン番号, 'count': LEDの数}
    'LV1': {'pin': 20, 'count': 15},
    'LV2': {'pin': 21, 'count': 15},
    'LV3': {'pin': 22, 'count': 15},
    'LV4': {'pin': 23, 'count': 15},
}

# PWM LED設定
# ----------------------------------------------------------------
# PWM制御する単色LEDのGPIOピン (GP0は将来の拡張用に温存)
PWM_LED_PINS = [1, 2, 3, 4]
# PWM周波数 (Hz) - ちらつき防止のため1kHz以上を推奨
PWM_LED_FREQUENCY = 1000
# PWM最大デューティ比 (16bit PWM: 0-65535)
PWM_LED_MAX_DUTY = 65535
# フェード処理のステップ間隔 (ms)
PWM_FADE_STEP_INTERVAL_MS = 10
# 待機処理のチェック間隔 (ms)
PWM_WAIT_CHECK_INTERVAL_MS = 50
# ガンマ補正値 (人間の視覚特性に合わせた輝度補正)
PWM_LED_GAMMA = 2.2

# ポテンショメータ / ADC設定
# ----------------------------------------------------------------
# ボリュームコントロール用ポテンショメータのGPIOピン
POTENTIOMETER_PIN = 26
# DFPlayerの最大ボリューム値
DFPLAYER_MAX_VOLUME = 30
# ADC読み取り値の変化を検知するためのデッドゾーン
VOLUME_DEADZONE = 500

# システム / タイミング設定
# ----------------------------------------------------------------
# メインループのポーリング間隔 (ms)
MAIN_LOOP_POLLING_MS = 50
# アイドル状態に移行するまでの無操作時間 (ms)
IDLE_TIMEOUT_MS = 300000
# アイドル状態での自動再生間隔 (秒)
AUTO_PLAY_INTERVAL_SECONDS = 60

# ボタン操作の閾値設定 (ms)
# ----------------------------------------------------------------
# 短押しと判定する最大押下時間
BUTTON_SHORT_PRESS_MS = 500
# 長押しと判定する最小押下時間
BUTTON_LONG_PRESS_MS = 1000
# ダブルクリック判定の最大間隔
BUTTON_DOUBLE_CLICK_INTERVAL_MS = 500

# エラーハンドリング設定 (ms)
# ----------------------------------------------------------------
# メインループでエラーが発生した際の待機時間
ERROR_RETRY_DELAY_MS = 1000

# 内蔵LED設定
# ----------------------------------------------------------------
# 起動完了時の点滅回数
ONBOARD_LED_BLINK_TIMES = 2
# 点滅時の点灯時間 (ms)
ONBOARD_LED_ON_TIME_MS = 300
# 点滅時の消灯時間 (ms)
ONBOARD_LED_OFF_TIME_MS = 200

# OLED表示設定
# ----------------------------------------------------------------
# テキスト表示時の行の高さ (ピクセル)
OLED_LINE_HEIGHT = 10
# 最大表示行数
OLED_MAX_LINES = 4
# I2Cタイムアウト時のリトライ回数
OLED_I2C_RETRY_COUNT = 1

# ステッピングモーターのGPIOピン設定
STEPPER_MOTOR_CONFIG = {
    'AIN1': 9,    # AOUT1
    'AIN2': 10,   # AOUT2
    'BIN1': 11,   # BOUT1
    'BIN2': 15    # BOUT2
}
