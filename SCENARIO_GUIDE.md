# シナリオ作成ガイド

このドキュメントでは、`scenarios.json`を使用したシナリオの作成方法と、利用可能なすべてのコマンドについて詳しく説明します。

**📘 モード操作の詳細は [MODES.md](./MODES.md) を参照してください。**

---

## 📋 コマンド一覧表

全コマンドの概要です。詳細は各セクションを参照してください。

### サウンド

| コマンド | 形式 | 簡潔な説明 | 詳細 |
|---------|------|-----------|------|
| sound | リスト・辞書 | 音声ファイルを再生 | [→詳細](#1-サウンド再生) |

### NeoPixel LED（RGB LEDストリップ）

| コマンド | 形式 | 簡潔な説明 | 詳細 |
|---------|------|-----------|------|
| fill | 辞書 | 単色で塗りつぶし | [→詳細](#21-単色塗りつぶしfill) |
| fade | 辞書 | 色をフェード | [→詳細](#22-色のフェードfade) |
| off | 辞書 | 全消灯 | [→詳細](#23-全消灯off) |

### PWM LED（単色LED）

| コマンド | 形式 | 簡潔な説明 | 詳細 |
|---------|------|-----------|------|
| led_on | 辞書 | 点灯 | [→詳細](#31-点灯led_on) |
| led_off | 辞書 | 消灯 | [→詳細](#32-消灯led_off) |
| led_fade_in | 辞書 | フェードイン | [→詳細](#33-フェードインled_fade_in) |
| led_fade_out | 辞書 | フェードアウト | [→詳細](#34-フェードアウトled_fade_out) |

### サーボモーター

| コマンド | 型 | 簡潔な説明 | 詳細 |
|---------|-----|-----------|------|
| rotate | continuous | 速度指定で回転 | [→詳細](#41-連続回転型サーボcontinuous) |
| stop | continuous | 停止 | [→詳細](#41-連続回転型サーボcontinuous) |
| set_angle | position | 角度指定（0-180度） | [→詳細](#42-角度制御型サーボposition) |
| center | position | 90度に移動 | [→詳細](#42-角度制御型サーボposition) |
| stop_all | 共通 | 全サーボ停止 | [→詳細](#43-全サーボ共通コマンド) |
| center_all | 共通 | 全サーボセンター | [→詳細](#43-全サーボ共通コマンド) |

### ステッピングモーター

| コマンド | 形式 | 簡潔な説明 | 詳細 |
|---------|------|-----------|------|
| rotate | 辞書 | 角度指定で回転 | [→詳細](#51-角度指定回転rotate) |
| step | 辞書 | ステップ数指定で回転 | [→詳細](#52-ステップ数指定回転step) |

### 待機・システム制御

| コマンド | 形式 | 簡潔な説明 | 詳細 |
|---------|------|-----------|------|
| delay | リスト・辞書 | 待機時間 | [→詳細](#6-待機時間) |
| wait_ms | 辞書 | 待機時間（旧形式） | [→詳細](#62-wait_ms辞書形式) |
| stop_playback | 辞書 | 全モジュール停止 | [→詳細](#71-全モジュール停止stop_playback) |

### 繰り返し制御

| コマンド | 形式 | 簡潔な説明 | 詳細 |
|---------|------|-----------|------|
| repeat | 辞書 | コマンド群を繰り返す | [→詳細](#8-繰り返し制御) |

---

## 📖 シナリオファイルの構造

### 基本構造

`scenarios.json`は、複数のシナリオを定義するJSONファイルです。

```json
{
    "シナリオ名1": [
        コマンド1,
        コマンド2,
        ...
    ],
    "シナリオ名2": [
        コマンド1,
        コマンド2,
        ...
    ]
}
```

### シナリオの種類

#### 1. 通常シナリオ
任意の名前で定義できます。セレクトモードで選択可能です。

```json
{
    "my_effect": [
        ["sound", 2, 1],
        {"type": "led", "command": "fill", "strip": "LV1", "color": [255, 0, 0], "duration": 1000}
    ]
}
```

#### 2. ランダム再生シナリオ
**数字で始まる名前のシナリオは、通常モードでランダム再生対象になります。**

**📘 ランダム再生の詳細は [MODES.md](./MODES.md#通常モード) を参照してください。**

```json
{
    "random_scenarios": [
        "シナリオ名1",
        "シナリオ名2",
        "シナリオ名3"
    ]
}
```

---

## 🎵 コマンドリファレンス

### 1. サウンド再生

DFPlayer Miniを使用してSDカードから音声ファイルを再生します。

#### 1.1 リスト形式（推奨）

```json
["sound", フォルダ番号, ファイル番号]
```

#### パラメータ
- **フォルダ番号**: 1-99（SDカード内の`/01/`～`/99/`フォルダ）
- **ファイル番号**: 1-255（ファイル名: `001.mp3`～`255.mp3`）

#### 例
```json
["sound", 2, 1]
```
→ `/02/001.mp3`を再生

---

#### 1.2 辞書形式

```json
{"type": "sound", "folder": 2, "file": 1}
```

#### パラメータ
- **folder**: フォルダ番号（1-99）
- **file**: ファイル番号（1-255）

#### 例
```json
{"type": "sound", "folder": 3, "file": 5}
```
→ `/03/005.mp3`を再生

#### 注意事項
- MP3ファイルは指定フォルダに配置
- ファイル名は3桁ゼロパディング（`001.mp3`、`002.mp3`等）
- 再生中に次のコマンドに進みます（ノンブロッキング）
- 音声再生の完了を待つ場合は`delay`コマンドを併用

---

### 2. NeoPixel LED制御（RGB LEDストリップ）

WS2812B規格のRGB LEDストリップを制御します。

#### 2.1 単色塗りつぶし（fill）

```json
{"type": "led", "command": "fill", "strip": "LV1", "color": [255, 0, 0], "duration": 1000}
```

**パラメータ:**
- **strip**: `"LV1"`, `"LV2"`, `"LV3"`, `"LV4"`, `"all"`
- **color**: `[R, G, B]`（各0-255）
- **duration**: フェード時間（ミリ秒、省略時は即座に変化）

**例:**
```json
{"type": "led", "command": "fill", "strip": "all", "color": [0, 255, 0], "duration": 500}
```
→ 全ストリップを0.5秒かけて緑色にフェード

#### 2.2 色のフェード（fade）

```json
{"type": "led", "command": "fade", "strip": "LV1", "start_color": [0, 0, 0], "end_color": [255, 0, 0], "duration": 2000}
```

**パラメータ:**
- **strip**: ストリップ名（`"LV1"`～`"LV4"`, `"all"`）
- **start_color**: 開始色 `[R, G, B]`
- **end_color**: 終了色 `[R, G, B]`
- **duration**: フェード時間（ミリ秒）

**例:**
```json
{"type": "led", "command": "fade", "strip": "LV2", "start_color": [255, 0, 0], "end_color": [0, 0, 255], "duration": 1500}
```
→ LV2を赤から青へ1.5秒かけてフェード

#### 2.3 全消灯（off）

```json
{"type": "led", "command": "off"}
```

**パラメータ:**
なし（全ストリップを即座に消灯）

#### 2.4 旧形式（互換性維持）

レガシーコマンドも引き続き使用可能です。

```json
["effect", "fade", [15, 16, 17], [0, 0, 0], [255, 0, 0], 1200]
```

**パラメータ:**
- インデックス配列（グローバルインデックス0-59）
- 開始色 `[R, G, B]`
- 終了色 `[R, G, B]`
- フェード時間（ミリ秒）

#### 技術仕様
- **データ速度**: 800kHz（WS2812B規格）
- **色解像度**: RGB各8bit（0-255）
- **フェードステップ**: 10ms間隔
- **グローバルインデックス**: 0-59（LV1: 0-14, LV2: 15-29, LV3: 30-44, LV4: 45-59）
- **協調的キャンセル**: ボタン操作でフェード中断可能
- **色キャッシュ**: 各LEDの現在色を保持

---

### 3. PWM LED制御（単色LED）

PWM制御により単色LEDの明るさを調整します。

#### 3.1 点灯（led_on）

```json
{"led_on": {"led_index": 0, "max_brightness": 100}}
```

**パラメータ:**
- **led_index**: 0-3（GP1=0, GP2=1, GP3=2, GP4=3）
- **max_brightness**: 輝度（0-100%）

#### 3.2 消灯（led_off）

```json
{"led_off": {"led_index": 0}}
```

**パラメータ:**
- **led_index**: 0-3

#### 3.3 フェードイン（led_fade_in）

```json
{"led_fade_in": {"led_index": 0, "duration_ms": 1000, "max_brightness": 80}}
```

**パラメータ:**
- **led_index**: 0-3
- **duration_ms**: フェード時間（ミリ秒）
- **max_brightness**: 目標輝度（0-100%）

#### 3.4 フェードアウト（led_fade_out）

```json
{"led_fade_out": {"led_index": 0, "duration_ms": 1000}}
```

**パラメータ:**
- **led_index**: 0-3
- **duration_ms**: フェード時間（ミリ秒）

#### 技術仕様
- **PWM周波数**: 1kHz（ちらつき防止）
- **分解能**: 16bit PWM（0-65535）
- **ガンマ補正**: γ=2.2（人間の視覚特性に合わせた自然な明るさ変化）
- **フェードステップ**: 10ms間隔
- **協調的キャンセル**: ボタン操作でフェード中断可能
- **輝度キャッシュ**: 各LEDの現在輝度を保持

#### 注意事項
- **必ず電流制限抵抗（150-330Ω）を接続してください**
- 抵抗なしでLEDを直接接続すると、LEDおよびPicoボードが破損します

---

### 4. サーボモーター制御

サーボモーターは、`config.py`の`SERVO_CONFIG`で定義された型に応じて動作します。

#### サーボモーターの型

| 型 | 用途 | 制御方法 | コマンド |
|----|------|---------|---------|
| **continuous** | 連続回転型（SG90-HV等） | 速度指定 | `rotate`, `stop` |
| **position** | 角度制御型（SG90等） | 角度指定 | `set_angle`, `center` |

**設定例（config.py）:**
```python
SERVO_CONFIG = [
    [5, 'continuous'],  # GP5: 連続回転型
    [6, 'position'],    # GP6: 角度制御型
    [7, 'continuous']   # GP7: 連続回転型
]
```

---

#### 4.1 連続回転型サーボ（continuous）

##### rotate - 回転

```json
{"type": "servo", "command": "rotate", "servo_index": 0, "speed": 70, "duration_ms": 2000}
```

**パラメータ:**
- **servo_index**: 0-2（サーボ番号、設定順）
- **speed**: -100～100
  - -100: 最速反時計回り（CCW）
  - 0: 停止
  - 100: 最速時計回り（CW）
- **duration_ms**: 回転時間（ミリ秒、省略時は継続回転）

**例:**
```json
{"type": "servo", "command": "rotate", "servo_index": 0, "speed": 50, "duration_ms": 3000}
```
→ サーボ#0を50%の速度で3秒間回転

```json
{"type": "servo", "command": "rotate", "servo_index": 0, "speed": -80, "duration_ms": 0}
```
→ サーボ#0を80%の速度で逆回転（継続）

##### stop - 停止

```json
{"type": "servo", "command": "stop", "servo_index": 0}
```

**パラメータ:**
- **servo_index**: 0-2

---

#### 4.2 角度制御型サーボ（position）

##### set_angle - 角度設定

```json
{"type": "servo", "command": "set_angle", "servo_index": 1, "angle": 90}
```

**パラメータ:**
- **servo_index**: 0-2（サーボ番号、設定順）
- **angle**: 0～180（度）

**例:**
```json
{"type": "servo", "command": "set_angle", "servo_index": 1, "angle": 0}
```
→ サーボ#1を0度に移動

```json
{"type": "servo", "command": "set_angle", "servo_index": 1, "angle": 180}
```
→ サーボ#1を180度に移動

```json
{"type": "servo", "command": "set_angle", "servo_index": 1, "angle": 45}
```
→ サーボ#1を45度に移動

##### center - センター位置

```json
{"type": "servo", "command": "center", "servo_index": 1}
```

**パラメータ:**
- **servo_index**: 0-2

**動作:**
指定したサーボを90度（中央位置）に移動

---

#### 4.3 全サーボ共通コマンド

##### stop_all - 全停止

```json
{"type": "servo", "command": "stop_all"}
```

**パラメータ:**
なし

**動作:**
- 連続回転型: 停止（速度0）
- 角度制御型: 現在位置を保持

##### center_all - 全センター

```json
{"type": "servo", "command": "center_all"}
```

**パラメータ:**
なし

**動作:**
- 連続回転型: 停止
- 角度制御型: 90度に移動

---

#### 技術仕様
- **PWM周波数**: 50Hz（サーボモーター標準）
- **パルス幅範囲**: 1000-2000μs
  - **連続回転型**: 1000μs（最高速CCW）、1500μs（停止）、2000μs（最高速CW）
  - **角度制御型**: 1000μs（0度）、1500μs（90度）、2000μs（180度）
- **協調的キャンセル**: ボタン操作で中断可能
- **複数制御**: 最大3個を独立制御、型の混在可能

#### 注意事項
- **外部電源必須**（4.8-6.0V、各サーボ最大300mA）
- Picoの3.3Vや5V出力からは給電しないでください
- 外部電源のGNDとPicoのGNDを必ず接続
- サーボの型（continuous/position）は`config.py`で正しく設定してください

#### ステッピングモーターとの違い
| 項目 | サーボモーター | ステッピングモーター |
|------|---------------|---------------------|
| 制御方式 | 速度指定（continuous）<br>角度指定（position） | 角度・ステップ指定 |
| コマンド | `"type": "servo"` | `"type": "motor"` |
| 精度 | 中程度（連続回転は低い） | 高（ステップ単位） |
| 用途 | 連続回転、角度制御 | 精密な位置決め |

---

### 5. ステッピングモーター制御

ステッピングモーターを角度またはステップ数で制御します。

#### 5.1 角度指定回転（rotate）

```json
{"type": "motor", "command": "rotate", "angle": 90, "speed": "SLOW", "direction": 1}
```

**パラメータ:**
- **angle**: 回転角度（度）
- **speed**: `"VERY_SLOW"`, `"SLOW"`, `"NORMAL"`, `"FAST"`, `"VERY_FAST"` または数値（ミリ秒）
- **direction**: 1（正転）または -1（逆転）

**例:**
```json
{"type": "motor", "command": "rotate", "angle": 180, "speed": "NORMAL", "direction": -1}
```
→ 通常速度で180度逆転

```json
{"type": "motor", "command": "rotate", "angle": 360, "speed": "FAST", "direction": 1}
```
→ 高速で360度正転（1回転）

---

#### 5.2 ステップ数指定回転（step）

```json
{"type": "motor", "command": "step", "steps": 100, "direction": 1}
```

**パラメータ:**
- **steps**: ステップ数（1ステップ = 1.8度）
- **direction**: 1（正転）または -1（逆転）

**例:**
```json
{"type": "motor", "command": "step", "steps": 200, "direction": 1}
```
→ 200ステップ正転（360度 = 1回転）

```json
{"type": "motor", "command": "step", "steps": 50, "direction": -1}
```
→ 50ステップ逆転（90度）

---

#### 技術仕様
- **制御方式**: デジタル制御（Hブリッジドライバ経由）
- **ステップ解像度**: 200ステップ/回転（1.8度/ステップ）
- **速度レベル**: 5段階（VERY_SLOW=50ms, SLOW=20ms, NORMAL=10ms, FAST=5ms, VERY_FAST=2ms）
- **協調的キャンセル**: ボタン操作で回転中断可能
- **加減速制御**: 全体の10%を加速・減速区間とする

#### ステップ数と角度の対応表

| ステップ数 | 角度 | 回転 |
|-----------|------|------|
| 50 | 90° | 1/4回転 |
| 100 | 180° | 1/2回転 |
| 200 | 360° | 1回転 |
| 400 | 720° | 2回転 |

---

### 6. 待機時間

#### 6.1 delay（配列形式）

```json
["delay", ミリ秒]
```

**例:**
```json
["delay", 3000]
```
→ 3秒待機

#### 6.2 wait_ms（辞書形式）

```json
{"wait_ms": ミリ秒}
```

**例:**
```json
{"wait_ms": 500}
```
→ 0.5秒待機

#### 6.3 type: delay（辞書形式）

```json
{"type": "delay", "duration": ミリ秒}
```

**例:**
```json
{"type": "delay", "duration": 2000}
```
→ 2秒待機

#### 注意事項
- いずれの形式も**協調的キャンセル対応**（ボタン操作で中断可能）
- 待機中もシステムは応答性を保持

---

### 7. システム制御

#### 7.1 全モジュール停止（stop_playback）

```json
{"type": "stop_playback"}
```

**パラメータ:**
なし

**動作:**
- サウンド再生を停止
- 全サーボモーターを停止
- NeoPixel LEDを消灯
- PWM LEDを消灯
- ステッピングモーターの通電を解除

**使用例:**

緊急停止やシナリオのクリーンアップに使用

```json
"emergency_stop": [
    {"type": "stop_playback"},
    ["delay", 100]
]
```

---

### 8. 繰り返し制御

コマンド群を指定回数繰り返し実行します。同じパターンを何度も繰り返すシナリオを短く記述できます。

#### 8.1 基本形式（repeat）

```json
{"type": "repeat", "count": 回数, "commands": [コマンド配列]}
```

**パラメータ:**
- **count**: 繰り返し回数（1以上の整数、0で無限ループ）
- **commands**: 繰り返すコマンドの配列

**例1: LED点滅を10回繰り返す**
```json
{
    "led_blink_10": [
        {"type": "repeat", "count": 10, "commands": [
            {"type": "led", "command": "fill", "strip": "all", "color": [255, 0, 0]},
            {"type": "delay", "duration": 500},
            {"type": "led", "command": "off"},
            {"type": "delay", "duration": 500}
        ]}
    ]
}
```
→ 赤色LEDが0.5秒点灯→0.5秒消灯を10回繰り返す

**例2: 無限ループ（count: 0）**
```json
{
    "endless_animation": [
        {"type": "repeat", "count": 0, "commands": [
            {"type": "led", "command": "fade", "strip": "all", "start_color": [0, 0, 0], "end_color": [0, 255, 0], "duration": 1000},
            {"type": "led", "command": "fade", "strip": "all", "start_color": [0, 255, 0], "end_color": [0, 0, 0], "duration": 1000}
        ]}
    ]
}
```
→ ボタンで停止するまで緑色のフェードイン・アウトを繰り返す

**例3: サーボとLEDの複合繰り返し**
```json
{
    "servo_led_sync": [
        {"type": "repeat", "count": 5, "commands": [
            {"type": "servo", "command": "set_angle", "servo_index": 0, "angle": 0},
            {"type": "led", "command": "fill", "strip": "LV1", "color": [255, 0, 0]},
            {"wait_ms": 500},
            {"type": "servo", "command": "set_angle", "servo_index": 0, "angle": 180},
            {"type": "led", "command": "fill", "strip": "LV1", "color": [0, 0, 255]},
            {"wait_ms": 500}
        ]}
    ]
}
```
→ サーボ往復とLED色変更を同期させて5回繰り返す

#### 8.2 ネストした繰り返し

repeatコマンドは入れ子（ネスト）にできます。

```json
{
    "nested_pattern": [
        {"type": "repeat", "count": 3, "commands": [
            ["sound", 1, 1],
            {"type": "repeat", "count": 5, "commands": [
                {"type": "led", "command": "fill", "strip": "all", "color": [255, 255, 0]},
                {"type": "delay", "duration": 200},
                {"type": "led", "command": "off"},
                {"type": "delay", "duration": 200}
            ]},
            {"wait_ms": 1000}
        ]}
    ]
}
```
→ 「サウンド再生 → LED5回点滅 → 1秒待機」を3回繰り返す

#### 8.3 制限事項

**⚠️ 最大ネスト深度制限**

メモリ消費とスタックオーバーフローを防ぐため、ネストの深さには制限があります。

```
✅ 深度0: 最初のrepeat
  ✅ 深度1: ネストしたrepeat
    ✅ 深度2: さらにネストしたrepeat
      ❌ 深度3: エラー！最大深度を超過
```

**デフォルト**: 最大3レベルまで（`config.py`の`REPEAT_MAX_DEPTH`で変更可能）

深度を超過すると、以下のエラーメッセージがコンソールに出力され、シナリオが停止します:
```
[Error] Repeat nest depth exceeded (3 >= 3). Stopping.
```

#### ログ出力

繰り返し実行時、以下のログがコンソールに出力されます：

```
# 有限回の繰り返し
[Repeat] Iteration 1/30 (depth=0)
[Repeat] Iteration 2/30 (depth=0)
...

# 無限ループ（count: 0）
[Repeat] Infinite loop iteration 1 (depth=0)
[Repeat] Infinite loop iteration 2 (depth=0)
...

# ボタンで停止した場合
[Repeat] Stopped at iteration 15/30

# ネスト深度超過エラー
[Error] Repeat nest depth exceeded (3 >= 3). Stopping.
```

#### 注意事項
- **協調的キャンセル対応**: 繰り返し中もボタンで停止可能
- **無限ループ（count: 0）**: 必ずボタンで停止してください
- **パフォーマンス**: 大量の繰り返し（数千回以上）はメモリ消費に注意
- **デバッグ**: 上記のログで繰り返し状況を確認可能

---

## 🎨 実践的なシナリオ例

### 例1: 複合演出

```json
{
    "combined_effect": [
        ["sound", 2, 1],
        {"type": "led", "command": "fade", "strip": "all", "start_color": [0, 0, 0], "end_color": [255, 0, 0], "duration": 1000},
        {"led_fade_in": {"led_index": 0, "duration_ms": 500, "max_brightness": 80}},
        {"wait_ms": 500},
        {"type": "servo", "command": "rotate", "servo_index": 0, "speed": 70, "duration_ms": 2000},
        {"type": "motor", "command": "rotate", "angle": 90, "speed": "SLOW", "direction": 1},
        {"wait_ms": 2000},
        {"type": "servo", "command": "stop", "servo_index": 0},
        {"led_fade_out": {"led_index": 0, "duration_ms": 500}},
        {"type": "led", "command": "off"}
    ]
}
```

**このシナリオの動作:**
1. 音声再生（/02/001.mp3）
2. 全NeoPixelを黒から赤へ1秒かけてフェード
3. PWM LED #0を0.5秒でフェードイン（輝度80%）
4. 0.5秒待機
5. サーボ #0を速度70で2秒間回転
6. ステッピングモーターを90度正転（速度SLOW）
7. 2秒待機
8. サーボ #0を停止
9. PWM LED #0を0.5秒でフェードアウト
10. 全NeoPixel消灯

### 例2: マルチサーボ制御

```json
{
    "multi_servo": [
        {"type": "servo", "command": "rotate", "servo_index": 0, "speed": 50, "duration_ms": 1000},
        {"wait_ms": 200},
        {"type": "servo", "command": "rotate", "servo_index": 1, "speed": -70, "duration_ms": 1000},
        {"wait_ms": 200},
        {"type": "servo", "command": "rotate", "servo_index": 2, "speed": 100, "duration_ms": 1000},
        {"wait_ms": 1000},
        {"type": "servo", "command": "stop_all"}
    ]
}
```

**このシナリオの動作:**
1. サーボ #0を速度50で1秒回転
2. 0.2秒待機
3. サーボ #1を速度-70で1秒逆転
4. 0.2秒待機
5. サーボ #2を速度100で1秒回転
6. 1秒待機
7. 全サーボ停止

### 例3: LED同期パターン

```json
{
    "led_sync": [
        {"type": "led", "command": "fill", "strip": "LV1", "color": [255, 0, 0], "duration": 300},
        {"led_fade_in": {"led_index": 0, "duration_ms": 300, "max_brightness": 100}},
        {"wait_ms": 300},
        {"type": "led", "command": "fill", "strip": "LV2", "color": [0, 255, 0], "duration": 300},
        {"led_fade_in": {"led_index": 1, "duration_ms": 300, "max_brightness": 100}},
        {"wait_ms": 300},
        {"type": "led", "command": "fill", "strip": "LV3", "color": [0, 0, 255], "duration": 300},
        {"led_fade_in": {"led_index": 2, "duration_ms": 300, "max_brightness": 100}},
        {"wait_ms": 300},
        {"type": "led", "command": "fill", "strip": "LV4", "color": [255, 255, 0], "duration": 300},
        {"led_fade_in": {"led_index": 3, "duration_ms": 300, "max_brightness": 100}},
        {"wait_ms": 1000},
        {"type": "led", "command": "off"},
        {"led_off": {"led_index": 0}},
        {"led_off": {"led_index": 1}},
        {"led_off": {"led_index": 2}},
        {"led_off": {"led_index": 3}}
    ]
}
```

**このシナリオの動作:**
順番にNeoPixelとPWM LEDを点灯させる波紋効果

---

## 💡 ベストプラクティス

### 1. コマンド形式の選択

#### 推奨: 辞書形式（可読性が高い）
```json
{"type": "led", "command": "fill", "strip": "LV1", "color": [255, 0, 0], "duration": 1000}
```

#### レガシー: 配列形式（後方互換性のため残存）
```json
["effect", "fade", [0, 1, 2], [0, 0, 0], [255, 0, 0], 1000]
```

### 2. タイミング調整

- **音声とLEDの同期**: 音声再生直後に`wait_ms`を入れて音声の長さに合わせる
- **モーター動作の余裕**: 回転完了後に`wait_ms`を入れて振動が収まるのを待つ
- **フェードの重ね**: 複数のフェードを同時開始する場合、各コマンドの`duration`を調整

### 3. パフォーマンス

- **大量のLED制御**: グローバルインデックスより`strip`指定の方が効率的
- **連続コマンド**: 不要な`wait_ms: 0`は削除
- **音声ファイル**: 高ビットレートよりも適度な圧縮（128kbps程度）推奨

### 4. デバッグ

- **シナリオテスト**: セレクトモードで個別にテスト
- **ログ確認**: シリアルモニタでエラーメッセージを確認
- **段階的作成**: 少ないコマンドから始めて徐々に追加

---

## 📝 シナリオファイルのバリデーション

### よくあるエラー

#### 1. JSON構文エラー
```json
// ❌ 誤り: 最後のカンマ
{
    "test": [
        ["sound", 1, 1],
    ]
}

// ✅ 正しい
{
    "test": [
        ["sound", 1, 1]
    ]
}
```

#### 2. パラメータ不足
```json
// ❌ 誤り: speedがない
{"type": "servo", "command": "rotate", "servo_index": 0}

// ✅ 正しい
{"type": "servo", "command": "rotate", "servo_index": 0, "speed": 50}
```

#### 3. 範囲外の値
```json
// ❌ 誤り: 色が255を超える
{"type": "led", "command": "fill", "strip": "LV1", "color": [300, 0, 0]}

// ✅ 正しい
{"type": "led", "command": "fill", "strip": "LV1", "color": [255, 0, 0]}
```

### デバッグ方法

1. **シリアルモニタを開く**: エラーメッセージを確認
2. **最小構成でテスト**: コマンドを1つずつテスト
3. **JSONバリデータを使用**: オンラインツールで構文チェック
4. **ログ出力を追加**: `print()`でデバッグ情報を出力（開発時）

---

## 🔗 関連ドキュメント

- [README.md](./README.md) - プロジェクト概要と使い方
- [CONFIGURATION.md](./CONFIGURATION.md) - 設定方法の詳細
- [HARDWARE_NOTES.md](./HARDWARE_NOTES.md) - ハードウェア接続ガイド
- [ARCHITECTURE.md](./ARCHITECTURE.md) - システムアーキテクチャ
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 開発ガイドライン

---

## 📞 サポート

質問や問題がある場合は、シリアルモニタのログを確認し、必要に応じてGitHubのIssueを作成してください。
