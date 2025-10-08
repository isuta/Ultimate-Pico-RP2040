# データ駆動型 統合制御システム (NeoPixel/OLED/DFPlayer Mini)

このプロジェクトは、MicroPython環境（ESP32/ESP8266/RP2040など）で動作する、データ駆動型の統合制御システムです。LED、OLEDディスプレイ、およびオーディオ再生（DFPlayer Mini）の制御を、`scenarios.json` ファイルに基づいて実行します。

## 🚀 システムの概要

このシステムは、ハードウェアの配線や設定をすべて `config.py` に分離しており、新しいハードウェア構成への変更が容易です。

| モジュール | 役割 | 
 | ----- | ----- | 
| **NeoPixel** | 抽選結果やアニメーションの光演出 | 
| **OLED (SSD1306)** | ステータス、選択中のシナリオ、メッセージの表示 | 
| **DFPlayer Mini** | 効果音やBGMの再生 | 
| **タクトスイッチ** | 抽選開始、モード切替、シナリオ選択 | 

## ⚙️ セットアップと設定

### 1\. 必要なファイル

以下のファイルをMicroPythonデバイスにアップロードしてください。

**プロジェクトファイル (デバイスのルートディレクトリに配置):**

* `main.py`

* `config.py`

* `effects.py`

* `led_patterns.py`

* `oled_patterns.py`

* `sound_patterns.py`

* `scenarios.json`

**外部ライブラリ (Thonnyなどで`lib`フォルダに配置):**

* `ssd1306.py` (SSD1306 OLEDドライバ)

* `neopixel.py` (NeoPixel制御ライブラリ)

### 2\. ハードウェア設定 (`config.py`)

`config.py` ファイルを開き、ご自身の配線に合わせて以下の値を**正確に**設定してください。

| 設定項目 | 説明 | 変更範囲の例 | 
 | ----- | ----- | ----- | 
| `OLED_SDA_PIN`, `OLED_SCL_PIN` | OLED接続先のGPIOピン番号。 | `16`, `17` など | 
| `OLED_WIDTH`, `OLED_HEIGHT` | 使用するOLEDのピクセル数。 | `128`, `64` | 
| `DFPLAYER_TX_PIN`, `DFPLAYER_RX_PIN` | DFPlayer Mini接続先のUARTピン。 | `12`, `13` など | 
| `DFPLAYER_BUSY_PIN` | DFPlayerのBUSY信号が接続されたGPIOピン。 | `14` など | 
| `DFPLAYER_DEFAULT_VOLUME` | DFPlayerの初期音量。（0:ミュート 〜 30:最大） | `15` (推奨) | 
| `BUTTON_PIN` | タクトスイッチが接続されたGPIOピン。 | `18` など | 
| `NEOPIXEL_STRIPS` | 各NeoPixelストリップのピン番号とLED数。 | `'LV1': {'pin': 20, 'count': 6}` | 

### 3\. シナリオのカスタマイズ (`scenarios.json`)

すべての光と音の演出は `scenarios.json` にて定義されます。このファイルを編集することで、**Pythonコードを一切触らずに**新しい演出を追加できます。

#### シナリオキーのルール

* **`"1"`から始まる任意の整数（文字列）**で定義されたキー（例: `"1"`, `"2"`, `"36"`）が、ランダム再生の**抽選対象**となります。

* **数字以外のキー**（例: `"_101"`, `"_README_"`）は、システムやデバッグ用の予約キーと見なされ、演出再生の**抽選対象外**となります。

#### 利用可能なコマンドフォーマット

| コマンドタイプ | フォーマット | 説明 | 
 | ----- | ----- | ----- | 
| **`sound`** | `["sound", folder_num (int), file_num (int)]` | DFPlayer Miniの指定フォルダ/ファイル番号の音声を再生します。 | 
| **`delay`** | `["delay", duration_ms (int)]` | 演出の実行を一時停止します（ミリ秒単位）。停止フラグで中断可能です。 | 
| **`effect`** | `["effect", "off"]` | すべてのNeoPixel LEDを瞬時に消灯します。 | 
| **`effect`** | `["effect", "global_set", [indices (list)], R (int), G (int), B (int)]` | 指定された**グローバルLEDインデックス**に色を瞬時に設定します。 | 
| **`effect`** | `["effect", "fade", [indices (list)], [start_R, start_G, start_B], [end_R, end_G, end_B], duration_ms (int)]` | 指定時間かけて、開始色から終了色へ滑らかにフェードさせます。 | 
| **`effect` (旧式)** | `["effect", "local_set (旧式)", strip_name (str), led_index (int/"ALL"), R, G, B, duration_ms (int)]` | 従来のストリップ単位の設定。**非推奨**。duration\_msだけ点灯後に元に戻ります。 | 

## 🕹️ 基本的な使い方

システム起動後、タクトスイッチの操作によって2つのモードに切り替わります。

### 1\. 通常モード (初期状態)

OLEDに「Push the button」が表示されます。

  * **短押し**: ランダムなシナリオ（`scenarios.json`からランダムな番号）が選ばれ、演出が開始されます。

### 2\. セレクトモード (デバッグ/選択)

電源投入直後、**1秒以上ボタンを長押し**したまま起動すると、セレクトモードに入ります。OLEDに「Select Mode」と表示されます。

  * **短押し 1回**: 選択中のシナリオ番号が**次に進みます** (`1` → `2` → `3`...)。

  * **短押し 2回 (連続)**: 選択中のシナリオ番号が**前に戻ります** (`3` → `2` → `1`...)。

  * **長押し (1秒以上)**: 画面に表示されている**選択中のシナリオ**の演出を開始します。

  * **再生中の短押し**: 実行中の演出を強制的に停止させます。