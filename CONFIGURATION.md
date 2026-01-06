# 設定ガイド

このドキュメントでは、Ultimate-Pico-RP2040システムの全設定方法について詳しく説明します。

---

## 📋 目次

1. [config.pyの概要](#configpyの概要)
2. [GPIOピンの設定](#gpioピンの設定)
3. [ハードウェア設定](#ハードウェア設定)
4. [タイミング設定](#タイミング設定)
5. [システム動作設定](#システム動作設定)
6. [カスタマイズ例](#カスタマイズ例)

**📘 モード操作の詳細は [MODES.md](./MODES.md) を参照してください。**

---

## 📄 config.pyの概要

`config.py`は、システム全体の設定を一元管理するファイルです。すべてのモジュールがこのファイルから設定を読み込むため、カスタマイズが1箇所で完結します。

### ファイルの場所
```
Ultimate-Pico-RP2040/
  └─ config.py
```

### 基本原則
- **大文字の定数**: すべての設定は大文字の定数として定義
- **単位を明記**: 時間は`_MS`（ミリ秒）、周波数は`_FREQUENCY`等
- **デフォルト値**: 安全で実用的な値をデフォルトとして設定
- **コメント**: 各設定の説明を日本語で記載

---

## 🔌 GPIOピンの設定

### GPIO使用状況一覧

現在のGPIO割り当て（22ピン使用中、6ピン空き）:

| GPIO | 用途 | モジュール |
|------|------|-----------|
| **GP0** | **温存**（将来の拡張用） | - |
| GP1-4 | PWM LED制御 | pwm_led_controller |
| GP5-7 | サーボモーター制御 | servo_rotation_controller / servo_position_controller |
| **GP8** | **空き** | - |
| GP9-11, GP15 | ステッピングモーター | stepper_motor |
| GP12-14 | DFPlayer Mini（TX/RX/BUSY） | sound_patterns |
| GP16-17 | OLED I2C（SDA/SCL） | oled_patterns |
| GP18 | タクトスイッチ | state_manager |
| **GP19** | **空き** | - |
| GP20-23 | NeoPixel（LV1-4） | neopixel_controller |
| **GP24-25** | **空き** | - |
| GP26 | ポテンショメータ（ADC0） | volume_control |
| **GP27-28** | **空き** | - |

### PWM LED設定

```python
# config.py
PWM_LED_PINS = [1, 2, 3, 4]  # GP1-GP4
PWM_LED_FREQUENCY = 1000     # 1kHz（ちらつき防止）
PWM_LED_GAMMA = 2.2          # ガンマ補正値
```

**カスタマイズ:**
- **ピン変更**: リストの値を変更（例: `[2, 3, 4, 5]`でGP2-5を使用）
- **LED数変更**: リストの要素数を変更（例: `[1, 2]`で2個のみ使用）
- **周波数変更**: ちらつきが気になる場合は2000に増やす
- **ガンマ値**: 2.0-2.4の範囲で調整（2.2が標準）

### NeoPixel LED設定

```python
# config.py
NEOPIXEL_STRIPS = {
    'LV1': {'pin': 20, 'count': 15},
    'LV2': {'pin': 21, 'count': 15},
    'LV3': {'pin': 22, 'count': 15},
    'LV4': {'pin': 23, 'count': 15}
}
```

**カスタマイズ:**

#### LED数の変更
```python
NEOPIXEL_STRIPS = {
    'LV1': {'pin': 20, 'count': 30},  # 30個に変更
    'LV2': {'pin': 21, 'count': 15},
    'LV3': {'pin': 22, 'count': 15},
    'LV4': {'pin': 23, 'count': 15}
}
```

#### ストリップの削除
```python
NEOPIXEL_STRIPS = {
    'LV1': {'pin': 20, 'count': 15},
    'LV2': {'pin': 21, 'count': 15}
    # LV3, LV4は使用しない
}
```

#### ピン番号の変更
```python
NEOPIXEL_STRIPS = {
    'LV1': {'pin': 8, 'count': 15},   # GP8に変更
    'LV2': {'pin': 19, 'count': 15},  # GP19に変更
    'LV3': {'pin': 24, 'count': 15},  # GP24に変更
    'LV4': {'pin': 25, 'count': 15}   # GP25に変更
}
```

### サーボモーター設定

```python
# config.py
# サーボ設定 - [GPIOピン, サーボ型]
# サーボ型: 'continuous' (連続回転型) / 'position' (角度制御型)
SERVO_CONFIG = [
    [5, 'continuous'],  # Servo #0: GP5, 連続回転型
    [6, 'continuous'],  # Servo #1: GP6, 連続回転型
    [7, 'continuous']   # Servo #2: GP7, 連続回転型
]
SERVO_FREQUENCY = 50         # 50Hz（サーボモーター標準）
SERVO_ROTATION_CHECK_INTERVAL_MS = 50  # 回転チェック間隔
```

**カスタマイズ:**

#### サーボ数の変更
```python
SERVO_CONFIG = [
    [5, 'continuous'],  # 2個のみ使用
    [6, 'continuous']
]
# または
SERVO_CONFIG = [
    [5, 'position']  # 1個のみ使用
]
```

#### ピン番号と型の変更
```python
SERVO_CONFIG = [
    [8, 'position'],      # GP8で角度制御
    [19, 'continuous'],   # GP19で連続回転
    [24, 'continuous']    # GP24で連続回転
]
```

#### 型の混在（連続回転型と角度制御型を同時使用）
```python
SERVO_CONFIG = [
    [5, 'continuous'],  # GP5: 連続回転型（速度制御）
    [6, 'position'],    # GP6: 角度制御型（角度指定）
    [7, 'position']     # GP7: 角度制御型（角度指定）
]
```

**⚠️ 注意:**
- SERVO_FREQUENCYは50Hzから変更しないでください（サーボモーター規格）
- チェック間隔は50-100msが推奨

### ステッピングモーター設定

```python
# config.py
MOTOR_AIN1 = 9
MOTOR_AIN2 = 10
MOTOR_BIN1 = 11
MOTOR_BIN2 = 15
```

**カスタマイズ:**
```python
# 空きピンに移動する場合
MOTOR_AIN1 = 8
MOTOR_AIN2 = 19
MOTOR_BIN1 = 24
MOTOR_BIN2 = 25
```

### DFPlayer Mini設定

```python
# config.py
UART_TX_PIN = 12
UART_RX_PIN = 13
BUSY_PIN = 14
UART_BAUDRATE = 9600
```

**カスタマイズ:**
- UARTピンは限定的（GP0/1, GP4/5, GP8/9, GP12/13, GP16/17など）
- UART1を使用する場合: `UART_TX_PIN = 8`, `UART_RX_PIN = 9`
- UART_BAUDRATEは9600推奨（DFPlayerのデフォルト）

### OLED設定

```python
# config.py
OLED_SDA_PIN = 16
OLED_SCL_PIN = 17
I2C_FREQUENCY = 400000  # 400kHz
```

**カスタマイズ:**
- I2Cピンは限定的（GP0/1, GP2/3, GP4/5, GP6/7, GP8/9, GP10/11, GP14/15, GP16/17, GP18/19, GP20/21など）
- I2C0を使用する場合: `OLED_SDA_PIN = 0`, `OLED_SCL_PIN = 1`
- I2C_FREQUENCYは100000-400000の範囲

### ボタン設定

```python
# config.py
BUTTON_PIN = 18
```

**カスタマイズ:**
```python
BUTTON_PIN = 19  # 空きピンに変更
```

### ポテンショメータ設定

```python
# config.py
VOLUME_POT_PIN = 26  # ADC0
```

**カスタマイズ:**
- ADCピンはGP26-28のみ使用可能
- `VOLUME_POT_PIN = 27`（ADC1）または`28`（ADC2）

---

## ⚙️ ハードウェア設定

### フェード処理設定

```python
# config.py
PWM_FADE_STEP_INTERVAL_MS = 10  # フェードステップ間隔
NEOPIXEL_FADE_STEP_INTERVAL_MS = 10
```

**カスタマイズ:**
- **滑らかさ重視**: 5ms（負荷増加）
- **パフォーマンス重視**: 20ms（カクカクする可能性）
- **デフォルト**: 10ms（バランス良好）

### PWM解像度設定

```python
# config.py
PWM_LED_MAX_DUTY = 65535  # 16bit PWM
```

**通常は変更不要**（Pico RP2040の仕様）

---

## ⏱️ タイミング設定

### ボタン操作設定

```python
# config.py
BUTTON_SHORT_PRESS_MS = 500         # 短押し判定時間
BUTTON_LONG_PRESS_MS = 1000         # 長押し判定時間
BUTTON_DOUBLE_CLICK_INTERVAL_MS = 500  # ダブルクリック判定間隔
```

**📘 ボタン操作の詳細な動作は [MODES.md](./MODES.md) を参照してください。**

**カスタマイズ例:**

#### 反応速度を上げる（素早い操作）
```python
BUTTON_SHORT_PRESS_MS = 300
BUTTON_LONG_PRESS_MS = 700
BUTTON_DOUBLE_CLICK_INTERVAL_MS = 300
```

#### 誤操作を防ぐ（ゆっくり操作）
```python
BUTTON_SHORT_PRESS_MS = 700
BUTTON_LONG_PRESS_MS = 1500
BUTTON_DOUBLE_CLICK_INTERVAL_MS = 700
```

### アイドル・自動再生設定

```python
# config.py
IDLE_TIMEOUT_MS = 300000          # 5分（アイドル移行まで）
AUTO_PLAY_INTERVAL_SECONDS = 60   # 1分（自動再生間隔）
```

**📘 モード別の動作については [MODES.md](./MODES.md) を参照してください。**

**カスタマイズ例:**

#### 頻繁に自動再生
```python
IDLE_TIMEOUT_MS = 60000           # 1分でアイドル
AUTO_PLAY_INTERVAL_SECONDS = 30   # 30秒ごとに再生
```

#### 自動再生を減らす
```python
IDLE_TIMEOUT_MS = 600000          # 10分でアイドル
AUTO_PLAY_INTERVAL_SECONDS = 300  # 5分ごとに再生
```

#### 自動再生を無効化
```python
IDLE_TIMEOUT_MS = 999999999       # 実質無効
AUTO_PLAY_INTERVAL_SECONDS = 999999999
```

### ループ処理設定

```python
# config.py
LOOP_INTERVAL_MS = 50  # メインループの実行間隔
```

**カスタマイズ:**
- **応答性重視**: 20ms（負荷増加）
- **省電力重視**: 100ms（ボタン反応が鈍くなる）
- **デフォルト**: 50ms（バランス良好）

---

## 🎛️ システム動作設定

### ボリューム設定

```python
# config.py
VOLUME_MIN = 1      # 最小音量（DFPlayer範囲）
VOLUME_MAX = 30     # 最大音量（DFPlayer範囲: 0-30）
VOLUME_DEFAULT = 15 # デフォルト音量
```

**カスタマイズ例:**

#### 音量範囲を制限
```python
VOLUME_MIN = 5      # 最小を上げる（静かすぎる場合）
VOLUME_MAX = 20     # 最大を下げる（うるさすぎる場合）
VOLUME_DEFAULT = 12
```

#### 広い音量範囲
```python
VOLUME_MIN = 1
VOLUME_MAX = 30     # DFPlayerの最大
VOLUME_DEFAULT = 15
```

### DFPlayerタイムアウト設定

```python
# config.py
DFPLAYER_TIMEOUT_MS = 2000  # 初期化タイムアウト
```

**カスタマイズ:**
- **素早い起動**: 1000ms（初期化失敗リスク増加）
- **確実な初期化**: 3000ms（起動時間増加）
- **デフォルト**: 2000ms（バランス良好）

---

## 🎨 カスタマイズ例

### 例1: コンパクト構成（最小限のハードウェア）

```python
# config.py

# PWM LED: 2個のみ
PWM_LED_PINS = [1, 2]

# NeoPixel: 1ストリップのみ
NEOPIXEL_STRIPS = {
    'LV1': {'pin': 20, 'count': 15}
}

# サーボ: なし
SERVO_CONFIG = []

# ボタン反応を速く
BUTTON_SHORT_PRESS_MS = 300
BUTTON_LONG_PRESS_MS = 700

# 自動再生を無効化
IDLE_TIMEOUT_MS = 999999999
```

### 例2: 大規模LED構成

```python
# config.py

# PWM LED: 最大4個
PWM_LED_PINS = [1, 2, 3, 4]

# NeoPixel: 各ストリップ30個
NEOPIXEL_STRIPS = {
    'LV1': {'pin': 20, 'count': 30},
    'LV2': {'pin': 21, 'count': 30},
    'LV3': {'pin': 22, 'count': 30},
    'LV4': {'pin': 23, 'count': 30}
}

# フェードを滑らかに
PWM_FADE_STEP_INTERVAL_MS = 5
NEOPIXEL_FADE_STEP_INTERVAL_MS = 5
```

### 例3: モーター重視構成

```python
# config.py

# サーボ: 3個フル活用（連続回転型）
SERVO_CONFIG = [
    [5, 'continuous'],
    [6, 'continuous'],
    [7, 'continuous']
]

# ステッピングモーター: 有効
MOTOR_AIN1 = 9
MOTOR_AIN2 = 10
MOTOR_BIN1 = 11
MOTOR_BIN2 = 15

# NeoPixel: 使用しない
NEOPIXEL_STRIPS = {}

# PWM LED: 使用しない
PWM_LED_PINS = []
```

### 例4: 展示用自動再生

```python
# config.py

# 短時間でアイドル移行
IDLE_TIMEOUT_MS = 30000  # 30秒

# 頻繁に自動再生
AUTO_PLAY_INTERVAL_SECONDS = 20  # 20秒ごと

# ボタン操作を簡単に
BUTTON_SHORT_PRESS_MS = 700
BUTTON_LONG_PRESS_MS = 1500
```

---

## 🔍 設定の確認方法

### シリアルモニタでの確認

起動時のログに各モジュールの状態が表示されます：

```
=== System Ready ===
Button: Available / Console Mode
OLED: Available
Audio: Available
LED: Available
PWM LED: Available
Servo: Available
Stepper Motor: Available
Onboard LED: Available
Volume Control: Available
===================
```

### 個別モジュールのテスト

#### PWM LEDのテスト
```json
{
    "test_pwm": [
        {"led_fade_in": {"led_index": 0, "duration_ms": 500, "max_brightness": 100}},
        {"wait_ms": 1000},
        {"led_fade_out": {"led_index": 0, "duration_ms": 500}}
    ]
}
```

#### NeoPixelのテスト
```json
{
    "test_neopixel": [
        {"type": "led", "command": "fill", "strip": "LV1", "color": [255, 0, 0], "duration": 500},
        {"wait_ms": 1000},
        {"type": "led", "command": "off"}
    ]
}
```

#### サーボのテスト
```json
{
    "test_servo": [
        {"type": "servo", "command": "rotate", "servo_index": 0, "speed": 50, "duration_ms": 2000},
        {"wait_ms": 500},
        {"type": "servo", "command": "stop", "servo_index": 0}
    ]
}
```

---

## ⚠️ 注意事項とトラブルシューティング

### GPIO競合の回避

**同じGPIOに複数の機能を割り当てないでください。**

❌ 誤り:
```python
PWM_LED_PINS = [1, 2, 3, 4]
SERVO_CONFIG = [
    [3, 'continuous'],  # GP3が重複！
    [4, 'continuous'],  # GP4が重複！
    [5, 'continuous']
]
```

✅ 正しい:
```python
PWM_LED_PINS = [1, 2, 3, 4]
SERVO_CONFIG = [
    [5, 'continuous'],  # 重複なし
    [6, 'continuous'],
    [7, 'continuous']
]
```

### PWMチャネルの競合

**同じPWMチャネルを共有するピンは同時に使用できません。**

RP2040のPWMチャネル割り当て:
- PWM0: GP0(A), GP1(B), GP16(A), GP17(B)
- PWM1: GP2(A), GP3(B), GP18(A), GP19(B)
- PWM2: GP4(A), GP5(B), GP20(A), GP21(B)
- PWM3: GP6(A), GP7(B), GP22(A), GP23(B)
- PWM4: GP8(A), GP9(B), GP24(A), GP25(B)
- PWM5: GP10(A), GP11(B), GP26(A), GP27(B)
- PWM6: GP12(A), GP13(B), GP28(A)
- PWM7: GP14(A), GP15(B)

同じ番号の(A)と(B)は異なる周波数で使用できません。

### I2C/UARTピンの制約

**I2CとUARTは特定のピンペアでのみ使用可能です。**

データシートを参照して適切なピンを選択してください。

### 電源容量の確認

**複数のハードウェアを同時使用する場合、電源容量に注意してください。**

- NeoPixel: 1個あたり最大60mA
- サーボモーター: 1個あたり最大300mA
- PWM LED: 1個あたり約10-20mA（抵抗値による）

外部電源の使用を検討してください（特にサーボモーター）。

---

## 🔗 関連ドキュメント

- [README.md](./README.md) - プロジェクト概要
- [SCENARIO_GUIDE.md](./SCENARIO_GUIDE.md) - シナリオ作成ガイド
- [HARDWARE_NOTES.md](./HARDWARE_NOTES.md) - ハードウェア接続ガイド
- [ARCHITECTURE.md](./ARCHITECTURE.md) - システムアーキテクチャ
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 開発ガイドライン

---

## 📞 サポート

設定に関する質問や問題がある場合は、以下を確認してください：
1. シリアルモニタのエラーメッセージ
2. GPIO使用状況一覧（競合確認）
3. ハードウェアの物理的な接続

必要に応じてGitHubのIssueを作成してください。
