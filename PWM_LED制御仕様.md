# LED制御システム追加仕様書

## 1. 概要

本システムは、Raspberry Pi Picoの空きGPIOピン（**GP1～GP4**）に接続された単色LEDを、PWMを用いて高精度かつ柔軟に制御するために導入されます。

### 最大の特徴
- **JSON（Python辞書）ベースのシナリオ定義**
- **ノンブロッキングな実行**
- **最優先でのシナリオ割り込み**
- **複数LED対応**: 最大4個のLEDを独立制御可能

これにより、LEDのフェード中や点滅中でも、モーター制御やDFPlayerの処理など、他の重要なタスクをメインループで同時に実行できます。

### GPIO割り当て
| GPIO | PWMチャネル | 物理ピン | 用途 |
|------|------------|---------|------|
| GP1 | PWM0_B | 2 | PWM LED #0 |
| GP2 | PWM1_A | 4 | PWM LED #1 |
| GP3 | PWM1_B | 5 | PWM LED #2 |
| GP4 | PWM2_A | 6 | PWM LED #3 |

**注**: GP0は将来の拡張用に温存します。

---

## 2. 影響ファイルと役割

| ファイル名 | 役割 | 変更点 |
|-----------|------|--------|
| `config.py` | ハードウェア定義 | 新しいPWM LEDピン配列 (`PWM_LED_PINS = [1, 2, 3, 4]`)、PWM周波数 (`PWM_LED_FREQUENCY`)、フェード・待機の間隔設定を追加 |
| **`pwm_led_controller.py`** | **PWM LED制御ロジック（新規作成）** | **PWM LEDの初期化、輝度設定、フェード処理を行う関数群を定義（ブロッキング方式、`stop_flag_ref`対応）** |
| `led_patterns.py` → **`neopixel_controller.py`** | **NeoPixel制御ロジック（リネーム）** | **ファイル名を変更してNeoPixel専用であることを明確化** |
| `system_init.py` | システム初期化 | `neopixel_controller`のインポート文修正、`pwm_led_controller`の初期化を追加 |
| `effects.py` | エフェクト実行エンジン | `neopixel_controller`のインポート文修正、PWM LEDコマンド処理（`led_on`, `led_off`, `led_fade_in`, `led_fade_out`）を追加 |
| `state_manager.py` | 状態管理 | PWM LED用の停止フラグ管理、シナリオ切り替えメソッドを追加（オプション） |
| `main.py` | メインアプリケーション | `pwm_led_controller`のインポートと初期化処理を追加 |

### リネーム対応の詳細

#### `led_patterns.py` → `neopixel_controller.py`
- **対象ファイル**: 2ファイル
  - `system_init.py`: インポート文と関数呼び出し（約4箇所）
  - `effects.py`: インポート文と関数呼び出し（約5箇所）
- **変更内容**: 
  ```python
  # 変更前
  import led_patterns
  led_patterns.init_neopixels()
  
  # 変更後
  import neopixel_controller
  neopixel_controller.init_neopixels()
  ```
- **影響**: インポート文と関数呼び出しの機械的な置換のみ（ロジック変更なし）

---

## 3. シナリオ定義とファイル統合

### シナリオファイル構成

PWM LEDのシナリオは、**既存の`scenarios.json`に統合**します。

**理由:**
1. **ランダム再生との互換性**: 既存の`random_scenarios`に自動的に含まれる
2. **複合演出が可能**: サウンド、NeoPixel、モーター、PWM LEDを1つのシナリオで組み合わせ可能
3. **実装がシンプル**: `effects.py`にPWM LEDコマンド処理を追加するだけ
4. **ユーザー体験の一貫性**: すべてのシナリオが同じファイル、同じ操作方法

### シナリオ例：複合演出

```json
{
    "combined_effect": [
        ["sound", 2, 1],
        {"led_fade_in": {"led_index": 0, "duration_ms": 500, "max_brightness": 80}},
        ["effect", "fade", [0,1,2], [0,0,0], [255,0,0], 1000],
        {"type": "motor", "command": "rotate", "angle": 90, "speed": "SLOW", "direction": 1},
        {"wait_ms": 1000},
        {"led_fade_out": {"led_index": 0, "duration_ms": 500}}
    ]
}
```

このシナリオは以下を同時実行します：
- サウンド再生（DFPlayer）
- PWM LED #0 のフェードイン
- NeoPixel LED 0-2 の赤色フェード
- ステッピングモーター90度回転
- 1秒待機
- PWM LED #0 のフェードアウト

### `effects.py`への実装

`execute_command()`関数にPWM LEDコマンド処理を追加：

```python
# effects.py の execute_command() 内に追加
import pwm_led_controller

def execute_command(command_list, stop_flag_ref):
    for cmd in command_list:
        # ... 既存の処理（sound, delay, motor, led等）...
        
        # PWM LED制御コマンドの追加
        if 'led_on' in cmd:
            params = cmd['led_on']
            led_index = params.get('led_index', 0)
            brightness = params.get('max_brightness', 100)
            if pwm_led_controller.is_pwm_led_available():
                pwm_led_controller.set_brightness(led_index, brightness)
        
        elif 'led_off' in cmd:
            params = cmd['led_off']
            led_index = params.get('led_index', 0)
            if pwm_led_controller.is_pwm_led_available():
                pwm_led_controller.set_brightness(led_index, 0)
        
        elif 'led_fade_in' in cmd:
            params = cmd['led_fade_in']
            led_index = params.get('led_index', 0)
            duration_ms = params['duration_ms']
            brightness = params.get('max_brightness', 100)
            if pwm_led_controller.is_pwm_led_available():
                pwm_led_controller.start_fade(led_index, brightness, duration_ms)
        
        elif 'led_fade_out' in cmd:
            params = cmd['led_fade_out']
            led_index = params.get('led_index', 0)
            duration_ms = params['duration_ms']
            if pwm_led_controller.is_pwm_led_available():
                pwm_led_controller.start_fade(led_index, 0, duration_ms)
        
        elif 'wait_ms' in cmd:
            duration_ms = cmd['wait_ms']
            # 既存のwait処理（ノンブロッキング）
            start_time = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
                if stop_flag_ref[0]:
                    return
                time.sleep_ms(50)
```

---

## 4. シナリオJSON定義仕様

LEDの動作パターンは、**既存の`scenarios.json`に追加**します。Python辞書（JSON形式）で定義されます。

### 4.1. トップレベルの構造

| キー | データ型 | 必須/任意 | 説明 |
|------|---------|----------|------|
| `name` | 文字列 | 必須 | シナリオの論理名（デバッグ・可読性のため） |
| `repeat` | 整数 | 任意 | シナリオ全体の繰り返し回数<br>- `1`：1回のみ実行（デフォルト）<br>- `3`：3回繰り返す<br>- `0` または `-1`：無限ループ（`stop_scenario`が呼ばれるまで） |
| `steps` | 配列 | 必須 | シナリオを構成するコマンドのリスト。上から順番に実行されます |

### 4.2. コマンド定義とパラメータ

**すべての動作時間指定はミリ秒（ms）で統一されます。**

| コマンドキー | 機能 | パラメータ（必須/任意） | 説明 |
|-------------|------|----------------------|------|
| `led_on` | 即時点灯 | `led_index` (任意, デフォルト: 0)<br>`max_brightness` (任意, デフォルト: 100) | 指定されたLED（0-3）を`max_brightness`で指定された輝度（0〜100）で即座に点灯します |
| `led_off` | 即時消灯 | `led_index` (任意, デフォルト: 0) | 指定されたLED（0-3）を即座に消灯します |
| `led_fade_in` | ブロッキングなフェードイン | `led_index` (任意, デフォルト: 0)<br>`duration_ms` (必須)<br>`max_brightness` (任意, デフォルト: 100) | 指定されたLEDを現在の輝度から`max_brightness`まで、`duration_ms`かけて滑らかに増加します。**停止フラグで中断可能** |
| `led_fade_out` | ブロッキングなフェードアウト | `led_index` (任意, デフォルト: 0)<br>`duration_ms` (必須) | 指定されたLEDを現在の輝度から0%まで、`duration_ms`かけて滑らかに減少します。**停止フラグで中断可能** |
| `wait_ms` | 待機（ブロッキング） | `duration_ms` (必須) | シナリオの進行を`duration_ms`間停止します。**停止フラグで中断可能** |
| `stop_playback` | 全モジュール停止 | なし | 現在実行中の全ての処理（音声、LED、モーター等）を停止します。次のコマンドから実行を再開します |

**注**: `led_index`を省略した場合、LED #0（GP1）が対象となります。複数LEDを同時制御する場合は、個別のコマンドを並べて記述します。

### 4.3. JSON定義例

#### 例1: 単一LED - 確認ダブル点滅を3回繰り返す

```json
{
    "name": "確認ダブル点滅",
    "repeat": 3,
    "steps": [
        {"led_on":  {"led_index": 0, "max_brightness": 100}},
        {"wait_ms": 100},
        {"led_off": {"led_index": 0}},
        {"wait_ms": 100},
        {"led_on":  {"led_index": 0, "max_brightness": 100}},
        {"wait_ms": 100},
        {"led_off": {"led_index": 0}},
        {"wait_ms": 800}
    ] 
}
```

#### 例2: 複数LED - 順次フェードイン

```json
{
    "name": "順次フェードイン",
    "repeat": 1,
    "steps": [
        {"led_fade_in": {"led_index": 0, "duration_ms": 500, "max_brightness": 80}},
        {"wait_ms": 200},
        {"led_fade_in": {"led_index": 1, "duration_ms": 500, "max_brightness": 80}},
        {"wait_ms": 200},
        {"led_fade_in": {"led_index": 2, "duration_ms": 500, "max_brightness": 80}},
        {"wait_ms": 200},
        {"led_fade_in": {"led_index": 3, "duration_ms": 500, "max_brightness": 80}},
        {"wait_ms": 1000},
        {"led_fade_out": {"led_index": 0, "duration_ms": 500}},
        {"led_fade_out": {"led_index": 1, "duration_ms": 500}},
        {"led_fade_out": {"led_index": 2, "duration_ms": 500}},
        {"led_fade_out": {"led_index": 3, "duration_ms": 500}}
    ]
}
```

#### 例3: 全LED同時点滅（停止フラグ活用）

```json
{
    "name": "全LED同時点滅",
    "repeat": 5,
    "steps": [
        {"led_on": {"led_index": 0, "max_brightness": 100}},
        {"led_on": {"led_index": 1, "max_brightness": 100}},
        {"led_on": {"led_index": 2, "max_brightness": 100}},
        {"led_on": {"led_index": 3, "max_brightness": 100}},
        {"wait_ms": 300},
        {"led_off": {"led_index": 0}},
        {"led_off": {"led_index": 1}},
        {"led_off": {"led_index": 2}},
        {"led_off": {"led_index": 3}},
        {"wait_ms": 300}
    ]
}
```
**注**: ボタン押下で即座に停止可能

#### 例4: BGM途中停止演出（stop_playback使用）

```json
{
    "name": "BGM途中停止演出",
    "repeat": 1,
    "steps": [
        ["sound", 2, 1],
        {"led_fade_in": {"led_index": 0, "duration_ms": 1000, "max_brightness": 80}},
        {"wait_ms": 8000},
        {"stop_playback": true},
        ["sound", 3, 1],
        {"led_fade_out": {"led_index": 0, "duration_ms": 500}}
    ]
}
```
**動作**: 30秒のBGMを8秒で強制停止し、効果音に切り替え

---

## 5. 動作原理（ブロッキング方式と停止フラグ）

### 5.1. ブロッキング実行（NeoPixelと同じ方式）

PWM LED制御は、既存のNeoPixel制御と同じ**ブロッキング方式**で実装します。

#### フェード処理
`led_fade_in`や`led_fade_out`が実行されると、指定された時間が経過するまで処理がブロックされます：

```python
def fade_pwm_led(led_index, start_brightness, end_brightness, duration_ms, stop_flag_ref):
    STEP_INTERVAL_MS = 10  # フェードの滑らかさ（調整可能）
    num_steps = duration_ms // STEP_INTERVAL_MS
    
    for step in range(num_steps):
        if stop_flag_ref[0]:  # 停止フラグチェック
            print("PWM LEDフェードを中断しました。")
            break
        
        # 輝度計算・PWM設定
        # ...
        
        time.sleep_ms(STEP_INTERVAL_MS)
```

#### 待機処理（wait_ms）
`wait_ms`コマンドも同様にブロッキングで実装され、停止フラグを定期的にチェックします：

```python
while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
    if stop_flag_ref[0]:
        return
    time.sleep_ms(50)  # チェック間隔（調整可能）
```

### 5.2. 停止フラグによる割り込み

#### 停止フラグの仕組み
- `stop_flag_ref[0]`は共有されるフラグ（リスト参照）
- シナリオ実行中、各ループで定期的にフラグをチェック
- フラグが`True`になると、処理を中断して終了

#### 応答時間
停止フラグによる中断は**協調的キャンセル**のため、以下の遅延が発生します：
- フェード処理: 最大 `STEP_INTERVAL_MS`（デフォルト10ms）
- 待機処理: 最大50ms
- **合計遅延**: 通常50～100ms程度

これらの値は`config.py`で調整可能です：
```python
PWM_FADE_STEP_INTERVAL_MS = 10  # 小さくすると応答性向上、CPU負荷増加
PWM_WAIT_CHECK_INTERVAL_MS = 50  # 小さくすると応答性向上、CPU負荷増加
```

#### 新しいシナリオへの切り替え
```python
# state_manager.py に追加するメソッド
def stop_and_start_pwm_scenario(self, new_scenario):
    """PWM LEDシナリオを停止して新しいシナリオを開始"""
    if self.is_pwm_led_playing:
        self.pwm_stop_flag[0] = True
        time.sleep_ms(100)  # 停止完了を待つ
    pwm_led_controller.start_scenario(new_scenario)
```

---

## 6. エラーハンドリング仕様

PWM LED制御は、既存のNeoPixelやDFPlayerと同じ**グレースフルデグラデーション**方式を採用します。

### 6.1. 初期化時のエラー処理

```python
# pwm_led_controller.py

pwm_leds = []  # PWMインスタンスのリスト
available_leds = set()  # 利用可能なLEDインデックス

def is_pwm_led_available():
    """PWM LEDが少なくとも1つ利用可能かどうかを返す"""
    return len(available_leds) > 0

def init_pwm_leds():
    """PWM LEDを初期化（失敗したピンはスキップ）"""
    global pwm_leds, available_leds
    
    pwm_leds = [None] * len(config.PWM_LED_PINS)
    available_leds = set()
    
    for i, pin_num in enumerate(config.PWM_LED_PINS):
        try:
            pin = Pin(pin_num)
            pwm = PWM(pin)
            pwm.freq(config.PWM_LED_FREQUENCY)
            pwm.duty_u16(0)  # 初期状態は消灯
            pwm_leds[i] = pwm
            available_leds.add(i)
            print(f"PWM LED #{i} on GP{pin_num} initialized.")
        except OSError as e:
            print(f"Warning: PWM LED #{i} on GP{pin_num} initialization failed: {e}")
            pwm_leds[i] = None
        except Exception as e:
            print(f"Error: PWM LED #{i} initialization error: {e}")
            pwm_leds[i] = None
    
    if len(available_leds) == 0:
        print("Warning: No PWM LEDs were successfully initialized. PWM LED functionality will be disabled.")
    else:
        print(f"PWM LED: {len(available_leds)}/{len(config.PWM_LED_PINS)} LEDs available")
```

### 6.2. ランタイムエラー処理

各関数で利用可否をチェックし、利用不可の場合はスキップします：

```python
def set_brightness(led_index, brightness):
    """指定されたLEDの輝度を設定"""
    if led_index not in available_leds:
        print(f"PWM LED #{led_index} is not available (skipped)")
        return False
    
    try:
        # 輝度変換とPWM設定
        # ...
        return True
    except OSError as e:
        print(f"[Hardware Error] PWM LED #{led_index} brightness set failed: {e}")
        return False
    except Exception as e:
        print(f"[Error] PWM LED #{led_index} error: {e}")
        return False
```

### 6.3. effects.pyでの使用例

```python
# effects.py の execute_command() 内
if 'led_on' in cmd:
    params = cmd['led_on']
    led_index = params.get('led_index', 0)
    brightness = params.get('max_brightness', 100)
    
    if pwm_led_controller.is_pwm_led_available():
        pwm_led_controller.set_brightness(led_index, brightness)
    else:
        print(f"PWM LED: LED #{led_index} 点灯（スキップ - PWM LED利用不可）")
```

### 6.4. システム起動時の状態表示

```python
# system_init.py に追加
print(f"PWM LED: {'OK' if pwm_led_controller.is_pwm_led_available() else 'N/A'}")
```

### 6.5. エラーハンドリングのポリシー

| エラー種別 | 処理方針 |
|-----------|---------|
| GPIO初期化失敗 | 該当LEDをスキップ、他のLEDは動作継続 |
| 全LED初期化失敗 | PWM LED機能を無効化、システムは継続動作 |
| ランタイムエラー | エラーログ出力、コマンドをスキップ、シナリオは継続 |
| 無効なLEDインデックス | ログ出力してスキップ |

---

## 8. config.py設定値の詳細仕様

PWM LED制御に必要な設定値を以下の通り定義します。

### 8.1. 基本設定

```python
# config.py

# PWM LED GPIO設定
PWM_LED_PINS = [1, 2, 3, 4]  # GP1-GP4を使用

# PWM設定
PWM_LED_FREQUENCY = 1000  # Hz（1kHz、ちらつき防止に十分な周波数）
PWM_LED_MAX_DUTY = 65535  # 16bit PWM（duty_u16の最大値）

# フェード・待機の応答性設定（NeoPixelと同じ値）
PWM_FADE_STEP_INTERVAL_MS = 10   # フェードのステップ間隔（ms）
PWM_WAIT_CHECK_INTERVAL_MS = 50  # 待機中の停止フラグチェック間隔（ms）

# ガンマ補正設定
PWM_LED_GAMMA = 2.2  # ガンマ補正値（1.0 = 補正なし/リニア変換、2.2 = 標準補正）
```

### 8.2. 各設定値の説明

| 設定項目 | デフォルト値 | 範囲 | 説明 |
|---------|------------|------|------|
| `PWM_LED_PINS` | `[1, 2, 3, 4]` | GP1-4 | PWM LED用のGPIOピン番号リスト |
| `PWM_LED_FREQUENCY` | `1000` | 100-10000 | PWM周波数（Hz）。1000Hz以上でちらつきなし |
| `PWM_LED_MAX_DUTY` | `65535` | 固定 | 16bit PWMの最大デューティ比（変更不要） |
| `PWM_FADE_STEP_INTERVAL_MS` | `10` | 5-50 | フェードの滑らかさ。小さいほど滑らか、CPU負荷増 |
| `PWM_WAIT_CHECK_INTERVAL_MS` | `50` | 10-100 | 停止フラグチェック間隔。小さいほど応答性高い、CPU負荷増 |
| `PWM_LED_GAMMA` | `2.2` | 0.5-3.0 | ガンマ補正値。1.0=補正なし、2.2=標準、0.5-0.9=明るめ |

### 8.3. 調整ガイドライン

#### PWM周波数（PWM_LED_FREQUENCY）
- **推奨**: 1000Hz（デフォルト）
- **変更が必要な場合**:
  - ちらつきが見える → 2000Hzに増やす
  - 他のデバイスとの干渉 → 500Hz-2000Hzの範囲で調整

#### フェード間隔（PWM_FADE_STEP_INTERVAL_MS）
- **推奨**: 10ms（NeoPixelと同じ）
- **調整例**:
  - より滑らかに → 5ms（CPU負荷2倍）
  - CPU負荷削減 → 20ms（やや粗いフェード）

#### 停止フラグチェック間隔（PWM_WAIT_CHECK_INTERVAL_MS）
- **推奨**: 50ms（NeoPixelと同じ）
- **調整例**:
  - 応答性重視 → 10ms（CPU負荷増）
  - CPU負荷削減 → 100ms（最大0.1秒の遅延）

#### ガンマ補正値（PWM_LED_GAMMA）
- **1.0**: 補正なし（リニア変換）
  - 数値通りのPWM値
  - 人間の目には暗く感じる
- **2.2**: 標準補正（推奨）
  - 業界標準値
  - 人間の目に自然な明るさ
  - 指定した輝度と見た目が一致
- **0.5-0.9**: 明るめ補正
  - LEDが暗すぎる場合に使用
  - PWM値を線形より明るく設定

### 8.4. 輝度変換の実装

```python
def brightness_to_duty(brightness):
    """
    輝度（0-100%）をPWMデューティ比（0-65535）に変換
    
    Args:
        brightness: 0-100（パーセント）
    
    Returns:
        duty: 0-65535（PWM duty値）
    """
    # 0-1.0に正規化
    normalized = brightness / 100.0
    
    # ガンマ補正適用
    corrected = normalized ** config.PWM_LED_GAMMA
    
    # PWM duty値に変換
    duty = int(corrected * config.PWM_LED_MAX_DUTY)
    
    return duty
```

**変換例（ガンマ2.2の場合）**:
- 輝度100% → duty 65535（100%）
- 輝度50% → duty 13107（20%）← 人間の目には50%に見える
- 輝度25% → duty 2621（4%）← 人間の目には25%に見える
- 輝度0% → duty 0（0%）

---

## 9. 既存シナリオとの並行実行ポリシー

PWM LED制御は、既存の全モジュール（NeoPixel、DFPlayer、ステッピングモーター）と**同じ停止フラグ（`stop_flag_ref`）を共有**します。

### 9.1. 停止フラグの共有

**全モジュールで統一された停止制御**：

```python
# state_manager.py で1つのstop_flagを管理
self.stop_flag = [False]

# effects.py でシナリオ実行時に全モジュールに渡す
execute_command(command_list, self.stop_flag)
```

### 9.2. 停止フラグの動作

シナリオ実行中、以下の全ての処理が**同じフラグ**をチェックします：

| モジュール | 処理 | 停止フラグチェック |
|-----------|------|------------------|
| **DFPlayer** | 音声再生 | 再生中に停止可能 |
| **NeoPixel** | フェード、点滅 | フェードループ内でチェック（10ms毎） |
| **ステッピングモーター** | 回転 | ステップ実行中にチェック |
| **PWM LED** | フェード、点滅 | フェードループ内でチェック（10ms毎） |
| **wait_ms** | 待機 | 待機中にチェック（50ms毎） |

**`stop_flag[0] = True`が設定されると、実行中の全ての処理が停止します。**

### 9.3. 停止方法

#### 方法1: ボタン押下による停止（既存機能）

```python
# state_manager.py
if self.is_playing:
    self.stop_flag[0] = True  # 全モジュールが停止
    self.is_playing = False
```

ユーザーがボタンを押すと、実行中の全ての処理（音声、LED、モーター等）が停止します。

#### 方法2: シナリオ内での停止（新規機能）

JSONシナリオ内で`stop_playback`コマンドを使用して、プログラム的に停止を制御できます：

```json
{
    "name": "BGM途中停止演出",
    "steps": [
        ["sound", 2, 1],                    
        {"led_fade_in": {"led_index": 0, "duration_ms": 1000, "max_brightness": 80}},
        {"wait_ms": 8000},                  
        {"stop_playback": true},            
        ["sound", 3, 1],                    
        {"led_fade_out": {"led_index": 0, "duration_ms": 500}}
    ]
}
```

**`stop_playback`コマンドの動作**：
1. 現在実行中の全ての処理を停止（音声、フェード、モーター等）
2. 停止完了を待機（最大100ms）
3. 停止フラグをリセット
4. 次のコマンドを実行

### 9.4. シナリオ実行の順序

**重要**: 現在のシステムは**ブロッキング方式**のため、シナリオ内のコマンドは**順次実行**されます：

```json
{
    "steps": [
        ["sound", 2, 1],           // ① 音声再生開始（非ブロッキング）
        {"led_fade_in": {...}},    // ② PWM LEDフェード開始（ブロッキング、完了まで待つ）
        ["effect", "fade", ...],   // ③ NeoPixelフェード（②完了後に開始）
        {"wait_ms": 1000}          // ④ 1秒待機（③完了後に開始）
    ]
}
```

**並行実行ではありません**：
- 音声再生のみ非ブロッキング（再生開始後すぐ次へ）
- LED、モーター、wait_msは順番に実行される
- 複数のフェードを同時実行したい場合は、それぞれ別のシナリオとして実行

### 9.5. 実装箇所

#### effects.py への追加

```python
# execute_command() 内に追加
def execute_command(command_list, stop_flag_ref):
    for cmd in command_list:
        # ... 既存の処理 ...
        
        # 停止コマンド処理（新規）
        if 'stop_playback' in cmd:
            print("Stopping all playback by scenario command...")
            stop_flag_ref[0] = True
            time.sleep_ms(100)  # 停止完了待ち
            stop_flag_ref[0] = False  # フラグリセット
            print("All playback stopped.")
            continue
        
        # PWM LEDコマンド処理
        if 'led_fade_in' in cmd:
            params = cmd['led_fade_in']
            if pwm_led_controller.is_pwm_led_available():
                pwm_led_controller.fade_pwm_led(
                    params.get('led_index', 0),
                    params.get('max_brightness', 100),
                    params['duration_ms'],
                    stop_flag_ref  # ← 同じフラグを渡す
                )
```

#### pwm_led_controller.py の実装

```python
def fade_pwm_led(led_index, target_brightness, duration_ms, stop_flag_ref):
    """PWM LEDフェード（停止フラグ対応）"""
    if led_index not in available_leds:
        return
    
    current_brightness = get_current_brightness(led_index)
    num_steps = duration_ms // config.PWM_FADE_STEP_INTERVAL_MS
    
    for step in range(num_steps):
        if stop_flag_ref[0]:  # ← 停止フラグチェック
            print(f"PWM LED #{led_index} フェードを中断しました。")
            return
        
        # 輝度計算とPWM設定
        progress = (step + 1) / num_steps
        brightness = current_brightness + (target_brightness - current_brightness) * progress
        set_brightness(led_index, brightness)
        
        time.sleep_ms(config.PWM_FADE_STEP_INTERVAL_MS)
```

### 9.6. 応答時間

停止フラグによる中断の最大遅延：
- **PWM LEDフェード**: 最大10ms（`PWM_FADE_STEP_INTERVAL_MS`）
- **NeoPixelフェード**: 最大10ms
- **wait_ms**: 最大50ms（`PWM_WAIT_CHECK_INTERVAL_MS`）
- **合計**: 通常50～100ms以内に全モジュールが停止

---

## 10. 実装タスクと実装順序

実装を安全かつ効率的に進めるため、以下の順序でタスクを実施します。

### 実装の原則
1. **既存機能を壊さない**: まずリネームと既存コードの整理から開始
2. **段階的な追加**: 基本機能から順に実装し、各段階でテスト
3. **依存関係を考慮**: 下位モジュールから上位モジュールへ

---

### フェーズ1: 準備作業（既存コードの整理）

#### タスク1-1: ファイルリネーム
**目的**: NeoPixel制御を明確化し、新規PWM LED制御と区別

**作業内容**:
```bash
# ファイルをリネーム
mv led_patterns.py neopixel_controller.py
```

**影響範囲**: 2ファイル
- `system_init.py`: インポート文修正（約4箇所）
- `effects.py`: インポート文修正（約5箇所）

**検証方法**:
- システム起動確認
- 既存NeoPixelシナリオの動作確認
- エラーログの確認

**所要時間**: 10分

---

#### タスク1-2: config.py設定値追加
**目的**: PWM LED用の設定値を定義

**作業内容**:
```python
# config.py の末尾に追加

# ============================================
# PWM LED設定
# ============================================
PWM_LED_PINS = [1, 2, 3, 4]  # GP1-GP4を使用
PWM_LED_FREQUENCY = 1000  # Hz（1kHz）
PWM_LED_MAX_DUTY = 65535  # 16bit PWM
PWM_FADE_STEP_INTERVAL_MS = 10   # フェードのステップ間隔（ms）
PWM_WAIT_CHECK_INTERVAL_MS = 50  # 待機中の停止フラグチェック間隔（ms）
PWM_LED_GAMMA = 2.2  # ガンマ補正値（1.0 = 補正なし）
```

**検証方法**:
- 構文エラーがないことを確認
- `import config`が成功することを確認

**所要時間**: 5分

---

### フェーズ2: PWM LED制御の基本実装

#### タスク2-1: pwm_led_controller.py 新規作成（基本機能）
**目的**: PWM LED制御の基盤を実装

**作業内容**:
1. モジュール変数の定義
   ```python
   pwm_leds = []
   available_leds = set()
   current_brightness = [0, 0, 0, 0]
   ```

2. 初期化関数の実装
   ```python
   def init_pwm_leds():
       # GPIO初期化、エラーハンドリング
   ```

3. 利用可否チェック関数
   ```python
   def is_pwm_led_available():
       return len(available_leds) > 0
   ```

4. 輝度変換関数
   ```python
   def brightness_to_duty(brightness):
       # ガンマ補正適用
   ```

5. 基本輝度設定関数
   ```python
   def set_brightness(led_index, brightness):
       # PWM duty設定
   ```

**検証方法**:
単体テストスクリプトを作成して動作確認

**test_pwm_basic.py**:
```python
# test_pwm_basic.py - PWM LED基本動作テスト
import config
import pwm_led_controller
import time

print("=== PWM LED Basic Test ===")

# 初期化
pwm_led_controller.init_pwm_leds()

if not pwm_led_controller.is_pwm_led_available():
    print("Error: No PWM LEDs available")
else:
    print(f"Available LEDs: {pwm_led_controller.available_leds}")
    
    # テスト1: 全LED順次点灯・消灯
    print("\nTest 1: Sequential ON/OFF")
    for i in range(4):
        if i in pwm_led_controller.available_leds:
            print(f"  LED {i}: ON (100%)")
            pwm_led_controller.set_brightness(i, 100)
            time.sleep(1)
            print(f"  LED {i}: OFF")
            pwm_led_controller.set_brightness(i, 0)
            time.sleep(0.5)
    
    # テスト2: 輝度レベルテスト（LED #0）
    print("\nTest 2: Brightness levels (LED #0)")
    if 0 in pwm_led_controller.available_leds:
        for brightness in [10, 25, 50, 75, 100]:
            print(f"  Brightness: {brightness}%")
            pwm_led_controller.set_brightness(0, brightness)
            time.sleep(1)
        pwm_led_controller.set_brightness(0, 0)
    
    # テスト3: ガンマ補正比較（LED #0）
    print("\nTest 3: Gamma correction comparison (LED #0)")
    if 0 in pwm_led_controller.available_leds:
        original_gamma = config.PWM_LED_GAMMA
        
        # ガンマ1.0（補正なし）
        config.PWM_LED_GAMMA = 1.0
        print(f"  Gamma 1.0 (linear): 50% brightness")
        pwm_led_controller.set_brightness(0, 50)
        time.sleep(2)
        
        # ガンマ2.2（標準補正）
        config.PWM_LED_GAMMA = 2.2
        print(f"  Gamma 2.2 (corrected): 50% brightness")
        pwm_led_controller.set_brightness(0, 50)
        time.sleep(2)
        
        pwm_led_controller.set_brightness(0, 0)
        config.PWM_LED_GAMMA = original_gamma

print("\n=== Test Complete ===")
```

**実行方法**:
```bash
# Raspberry Pi Pico に接続して実行
mpremote run test_pwm_basic.py
```

**所要時間**: 30分（実装） + 10分（テスト実行）

---

#### タスク2-2: system_init.py に初期化処理追加
**目的**: システム起動時にPWM LEDを初期化

**作業内容**:
```python
# system_init.py

import pwm_led_controller

def initialize_hardware():
    # ... 既存の初期化 ...
    
    # PWM LED初期化
    print("\n=== PWM LED Initialization ===")
    pwm_led_controller.init_pwm_leds()
    
    # ... 既存の初期化続き ...

def print_system_status():
    # ... 既存の出力 ...
    print(f"PWM LED: {'OK' if pwm_led_controller.is_pwm_led_available() else 'N/A'}")
```

**検証方法**:
- システム起動時のログ確認
- PWM LED初期化成功/失敗のメッセージ確認

**所要時間**: 10分

---

### フェーズ3: フェード機能の実装

#### タスク3-1: pwm_led_controller.py にフェード関数追加
**目的**: 滑らかなフェードイン/アウトを実装

**作業内容**:
```python
def fade_pwm_led(led_index, target_brightness, duration_ms, stop_flag_ref):
    """PWM LEDフェード（停止フラグ対応）"""
    # 現在輝度の取得
    # ステップ数計算
    # フェードループ（stop_flag_refチェック付き）
```

**検証方法**:
単体テストスクリプトで動作確認

**test_pwm_fade.py**:
```python
# test_pwm_fade.py - PWM LEDフェード機能テスト
import config
import pwm_led_controller
import time

print("=== PWM LED Fade Test ===")

# 初期化
pwm_led_controller.init_pwm_leds()
stop_flag = [False]  # ダミーの停止フラグ

if not pwm_led_controller.is_pwm_led_available():
    print("Error: No PWM LEDs available")
else:
    # テスト1: フェードイン・フェードアウト
    print("\nTest 1: Fade In/Out (LED #0)")
    if 0 in pwm_led_controller.available_leds:
        print("  Fade In (0% -> 100%, 2sec)")
        pwm_led_controller.fade_pwm_led(0, 100, 2000, stop_flag)
        time.sleep(0.5)
        
        print("  Fade Out (100% -> 0%, 2sec)")
        pwm_led_controller.fade_pwm_led(0, 0, 2000, stop_flag)
        time.sleep(0.5)
    
    # テスト2: 異なる速度でのフェード
    print("\nTest 2: Different fade speeds (LED #0)")
    if 0 in pwm_led_controller.available_leds:
        for duration in [500, 1000, 3000]:
            print(f"  Fade In ({duration}ms)")
            pwm_led_controller.fade_pwm_led(0, 80, duration, stop_flag)
            time.sleep(0.3)
            print(f"  Fade Out ({duration}ms)")
            pwm_led_controller.fade_pwm_led(0, 0, duration, stop_flag)
            time.sleep(0.3)
    
    # テスト3: 停止フラグによる中断
    print("\nTest 3: Stop flag interrupt (LED #0)")
    if 0 in pwm_led_controller.available_leds:
        import _thread
        
        def interrupt_after_delay():
            time.sleep(1)
            print("  [Interrupt] Setting stop_flag to True")
            stop_flag[0] = True
        
        print("  Starting 5-second fade...")
        stop_flag[0] = False
        _thread.start_new_thread(interrupt_after_delay, ())
        pwm_led_controller.fade_pwm_led(0, 100, 5000, stop_flag)
        print("  Fade interrupted!" if stop_flag[0] else "  Fade completed")
        
        # クリーンアップ
        pwm_led_controller.set_brightness(0, 0)
        stop_flag[0] = False

print("\n=== Test Complete ===")
```

**実行方法**:
```bash
mpremote run test_pwm_fade.py
```

**所要時間**: 20分（実装） + 10分（テスト実行）

---

### フェーズ4: effects.py への統合

#### タスク4-1: effects.py にPWM LEDコマンド処理追加
**目的**: JSONシナリオからPWM LEDを制御可能にする

**作業内容**:
1. インポート追加
   ```python
   import pwm_led_controller
   ```

2. `execute_command()` にコマンド処理追加
   ```python
   # led_on
   # led_off
   # led_fade_in
   # led_fade_out
   # stop_playback
   ```

**検証方法**:
- 各コマンドの個別テスト
- 複合シナリオのテスト（音声+PWM LED）
- stop_playback コマンドのテスト

**所要時間**: 30分

---

### フェーズ5: シナリオ定義と統合テスト

#### タスク5-1: scenarios.json にテストシナリオ追加
**目的**: 実際の使用例を作成して動作確認

**作業内容**:
```json
{
    "test_pwm_led_basic": [...],
    "test_pwm_led_fade": [...],
    "test_pwm_led_multi": [...],
    "test_combined": [...]
}
```

**検証方法**:
- セクション7のテスト項目を順次実行
- エラーケースのテスト（無効なLEDインデックス等）

**所要時間**: 40分

---

#### タスク5-2: パラメータ調整
**目的**: 最適な設定値を決定

**作業内容**:
- `PWM_FADE_STEP_INTERVAL_MS` の調整（5ms, 10ms, 20ms）
- `PWM_WAIT_CHECK_INTERVAL_MS` の調整（10ms, 50ms, 100ms）
- `PWM_LED_GAMMA` の比較（1.0 vs 2.2）
- CPU負荷の測定

**検証方法**:
- 各設定での動作確認
- 応答性のテスト
- 滑らかさの目視確認

**所要時間**: 30分

---

### 実装順序まとめ

| フェーズ | タスク | 実装時間 | テスト時間 | 累積時間 |
|---------|--------|---------|-----------|---------|
| **1** | 1-1: ファイルリネーム | 10分 | 5分 | 15分 |
| **1** | 1-2: config.py設定追加 | 5分 | - | 20分 |
| **2** | 2-1: pwm_led_controller.py基本実装 | 30分 | **10分** | 1時間 |
| **2** | 2-2: system_init.py統合 | 10分 | - | 1時間10分 |
| **3** | 3-1: フェード機能実装 | 20分 | **10分** | 1時間40分 |
| **4** | 4-1: effects.py統合 | 30分 | **15分** | 2時間25分 |
| **5** | 5-1: シナリオ定義とテスト | 40分 | - | 3時間5分 |
| **5** | 5-2: パラメータ調整 | 30分 | - | **3時間35分** |

**合計実装時間**: 約3時間35分（単体テスト含む）

**単体テストスクリプト**:
- `test_pwm_basic.py`: フェーズ2完了時に実行
- `test_pwm_fade.py`: フェーズ3完了時に実行
- 既存システムへの影響なく、PWM LED単体で動作確認可能

---

### 次のステップ

実装を開始しますか？最初のタスク（1-1: ファイルリネーム）から進めましょうか？

---

## 11. テスト項目

### フェーズ1: 既存ファイルのリネーム
1. `led_patterns.py` → `neopixel_controller.py` にリネーム
2. `system_init.py` のインポート文と関数呼び出しを修正
3. `effects.py` のインポート文と関数呼び出しを修正
4. 動作確認（既存機能が正常に動作することを確認）

---

## 11. テスト項目

以下のテスト項目を、実装フェーズごとに実施します。

### フェーズ2完了時のテスト

### 基本動作テスト
- [ ] 各LED（GP1-GP4）が個別に点灯・消灯できる
- [ ] PWM輝度制御（0-100%）が正しく動作する
- [ ] ガンマ補正の効果確認（1.0 vs 2.2の比較）
- [ ] GPIO初期化失敗時のエラーハンドリング動作確認

### フェーズ3完了時のテスト

### フェード機能テスト
- [ ] フェードイン・フェードアウトが滑らかに実行される
- [ ] 異なる duration_ms（500ms, 1000ms, 3000ms）での動作確認
- [ ] stop_flag による中断が正しく動作する

### フェーズ4完了時のテスト

### effects.py統合テスト
- [ ] `led_on` コマンドが正しく動作する
- [ ] `led_off` コマンドが正しく動作する
- [ ] `led_fade_in` コマンドが正しく動作する
- [ ] `led_fade_out` コマンドが正しく動作する
- [ ] `stop_playback` コマンドで全モジュールが停止する

### フェーズ5完了時のテスト

### 複合シナリオテスト
- [ ] PWM LED + NeoPixel の複合シナリオが動作する
- [ ] PWM LED + 音声再生 の複合シナリオが動作する
- [ ] PWM LED + モーター の複合シナリオが動作する
- [ ] ボタン押下で実行中のシナリオを停止できる

### 複数LED制御テスト
- [ ] 4個のLEDが独立して制御できる
- [ ] 順次フェードインが正しく動作する
- [ ] 全LED同時制御が正しく動作する

### 応答性テスト
- [ ] LED点滅中にボタン操作が可能（最大50～100ms遅延）
- [ ] LEDフェード中にNeoPixelシナリオを実行できる
- [ ] LEDフェード中にモーター制御が実行できる
- [ ] `PWM_FADE_STEP_INTERVAL_MS` による応答性の違いを確認
- [ ] `PWM_WAIT_CHECK_INTERVAL_MS` による応答性の違いを確認

### 既存機能の回帰テスト
- [ ] NeoPixel制御が正常に動作する（リネーム後）
- [ ] DFPlayer音声再生が正常に動作する
- [ ] ステッピングモーター制御が正常に動作する
- [ ] 既存シナリオがすべて正常に実行される
- [ ] ランダム再生機能が正常に動作する
- [ ] セレクトモードが正常に動作する

### エラーケーステスト
- [ ] 無効なLEDインデックス指定時のエラーハンドリング
- [ ] PWM LED利用不可時のスキップ動作確認
- [ ] 範囲外の輝度指定（-10, 150等）の処理確認
