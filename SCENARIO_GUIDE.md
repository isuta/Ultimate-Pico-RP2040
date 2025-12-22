# シナリオ作成ガイド

このドキュメントでは、`scenarios.json`を使用したシナリオの作成方法と、利用可能なすべてのコマンドについて詳しく説明します。

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
通常モードでボタンを押すと、これらからランダムに1つが選ばれます。

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

#### 形式
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

連続回転型サーボモーター（SG90-HV等）を制御します。

#### 4.1 回転（rotate）

```json
{"type": "servo", "command": "rotate", "servo_index": 0, "speed": 70, "duration_ms": 2000}
```

**パラメータ:**
- **servo_index**: 0-2（サーボ番号、GP5=0, GP6=1, GP7=2）
- **speed**: -100～100
  - -100: 最速反時計回り（CCW）
  - 0: 停止
  - 100: 最速時計回り（CW）
- **duration_ms**: 回転時間（ミリ秒、省略時は継続回転）

#### 4.2 停止（stop）

```json
{"type": "servo", "command": "stop", "servo_index": 0}
```

**パラメータ:**
- **servo_index**: 0-2

#### 4.3 全停止（stop_all）

```json
{"type": "servo", "command": "stop_all"}
```

**パラメータ:**
なし（全サーボを停止）

#### 技術仕様
- **PWM周波数**: 50Hz（サーボモーター標準）
- **パルス幅範囲**: 1000-2000μs
  - 1000μs: 最高速CCW
  - 1500μs: 停止
  - 2000μs: 最高速CW
- **協調的キャンセル**: ボタン操作で回転中断可能
- **複数制御**: 最大3個を独立制御

#### 注意事項
- **外部電源必須**（4.8-6.0V、各サーボ最大300mA）
- Picoの3.3Vや5V出力からは給電しないでください
- 外部電源のGNDとPicoのGNDを必ず接続

#### ステッピングモーターとの違い
| 項目 | サーボモーター | ステッピングモーター |
|------|---------------|---------------------|
| 制御方式 | 時間指定 | 角度指定 |
| コマンド | `"type": "servo"` | `"type": "motor"` |
| 精度 | 低（位置保持なし） | 高（ステップ単位） |
| 用途 | 連続回転、速度制御 | 精密な位置決め |

---

### 5. ステッピングモーター制御

ステッピングモーターを角度指定で制御します。

#### 回転（rotate）

```json
{"type": "motor", "command": "rotate", "angle": 90, "speed": "SLOW", "direction": 1}
```

**パラメータ:**
- **angle**: 回転角度（度）
- **speed**: `"VERY_SLOW"`, `"SLOW"`, `"NORMAL"`, `"FAST"`, `"VERY_FAST"`
- **direction**: 1（正転）または -1（逆転）

**例:**
```json
{"type": "motor", "command": "rotate", "angle": 180, "speed": "NORMAL", "direction": -1}
```
→ 通常速度で180度逆転

#### 技術仕様
- **制御方式**: デジタル制御（Hブリッジドライバ経由）
- **ステップ解像度**: 200ステップ/回転（1.8度/ステップ）
- **速度レベル**: 5段階
- **協調的キャンセル**: ボタン操作で回転中断可能

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
