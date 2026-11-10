# GMap2AppleMaps

用 Google Maps 找地點，用 Apple Maps 導航。

一個 iOS 捷徑（Shortcut）「**使用AppleMaps導航 (GPS)**」：在 Google Maps 按「分享」→ 選這個捷徑，就會取出該地點的 GPS 座標，直接在 Apple Maps 開啟開車導航。兼顧 Google 的圖資和 Apple Maps 的導航介面。

> An iOS Shortcut that takes a place shared from Google Maps, resolves its exact coordinates, and opens turn-by-turn directions in Apple Maps.

## 安裝

**方法一：iCloud 連結（推薦）**

在 iPhone 上打開：<!-- TODO: 換成你的 iCloud 分享連結 -->
https://www.icloud.com/shortcuts/d82e336b7b214dd38e212b3382254b0a

**方法二：下載檔案**

下載 [`使用AppleMaps導航 (GPS).shortcut`](<使用AppleMaps導航 (GPS).shortcut>)，在 iPhone 或 Mac 上打開即可加入。

第一次執行時，捷徑會詢問是否允許連線到 `maps.app.goo.gl` 和 `www.google.com`，選 **永遠允許**。

## 使用方式

- **Google Maps app**：打開地點 → 分享 → 選「使用AppleMaps導航 (GPS)」
- **任何 Google Maps 連結**：在 Safari、LINE 等地方長按連結 → 分享 → 選「使用AppleMaps導航 (GPS)」
- **純座標**：複製 `25.0339, 121.5644` 這類文字後直接執行捷徑（沒有輸入時會讀剪貼簿）

## 運作原理

1. 輸入的文字或網址裡如果已經有座標（電腦版連結的 `!3d…!4d…`、`@lat,lng`、純座標），直接使用。
2. iPhone 版 Google Maps 分享出來的短網址（`maps.app.goo.gl/…`）展開後是 `google.com/maps?q=地址店名&ftid=0x…:0x…`，**網址裡沒有座標**。捷徑會用電腦版瀏覽器的身分抓取頁面，取出地點的 `ftid`。
3. 拿 `ftid` 向 Google Maps 網頁版內部使用的地點查詢網址（`/maps/preview/place`）取得精準座標。
4. 用 `maps://?daddr=緯度,經度&dirflg=d` 開啟 Apple Maps 開車導航。

如果以上都失敗：網址裡有 `q=`（店名＋地址）時，改用 Apple Maps 搜尋；否則會跳出提示，並把除錯資訊複製到剪貼簿。

## 限制

- 第 3 步使用的是 **Google 未公開的內部查詢網址**，不是正式 API。Google 改版時可能失效。
- 需要網路連線。
- 只導向單一地點，不支援 Google Maps 的路線規劃連結（多個停靠點）。

遇到問題時，請把跳出提示後剪貼簿裡的除錯資訊貼到 [Issues](../../issues)。

## 自己產生捷徑檔

捷徑檔由 [`build_shortcut.py`](build_shortcut.py) 產生（只需要 Python 3 標準函式庫），每個動作和正規表示式都寫在裡面，方便檢查或修改。

```bash
python3 build_shortcut.py GMap2AppleMaps_unsigned.shortcut
# Apple 只接受簽章過的捷徑檔，需在 macOS 上簽章：
shortcuts sign --mode anyone -i GMap2AppleMaps_unsigned.shortcut -o "使用AppleMaps導航 (GPS).shortcut"
```

## License

MIT
