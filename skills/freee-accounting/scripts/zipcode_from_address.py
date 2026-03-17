#!/usr/bin/env python3
"""
住所から郵便番号を逆引きするスクリプト。

日本郵便の郵便番号データ（UTF-8版）を使用。
初回実行時にデータをダウンロードし、~/.cache/yoshinani/ にキャッシュする。

Usage:
  python zipcode_from_address.py "福岡県福岡市中央区天神4-7-6"
  python zipcode_from_address.py "東京都千代田区丸の内1-1-1"
"""
import csv
import re
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

# 日本郵便 UTF-8版 郵便番号データ
ZIP_URL = "https://www.post.japanpost.jp/zipcode/dl/utf/zip/utf_ken_all.zip"
CACHE_DIR = Path.home() / ".cache" / "yoshinani"
CACHE_ZIP = CACHE_DIR / "utf_ken_all.zip"
CACHE_CSV = CACHE_DIR / "utf_ken_all.csv"

# 都道府県リスト（検索用）
PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]


def ensure_data() -> Path:
    """郵便番号データをダウンロード・解凍してCSVパスを返す。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not CACHE_CSV.exists():
        urlretrieve(ZIP_URL, CACHE_ZIP)
        with zipfile.ZipFile(CACHE_ZIP, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".csv"):
                    zf.extract(name, CACHE_DIR)
                    extracted = CACHE_DIR / name
                    if extracted != CACHE_CSV:
                        extracted.rename(CACHE_CSV)
                    break

    return CACHE_CSV


def parse_address(addr: str) -> tuple[str | None, str | None, str | None]:
    """
    住所文字列から都道府県・市区町村・町域を抽出する。
    例: "福岡県福岡市中央区天神4-7-6" -> ("福岡県", "福岡市中央区", "天神")
    """
    addr = addr.strip().replace(" ", "").replace("　", "")

    # 都道府県を抽出
    prefecture = None
    rest = addr
    for pref in PREFECTURES:
        if addr.startswith(pref):
            prefecture = pref
            rest = addr[len(pref) :]
            break

    if not prefecture:
        return None, None, None

    # 番地（数字・ハイフン）の前までを市区町村・町域とする
    match = re.match(r"^(.+?)(\d[\d\-－ー・]*)$", rest)
    if match:
        rest = match.group(1)

    # 市区町村と町域を分割
    city_match = re.match(r"^(.+?市.+?区)(.*)$", rest)
    if city_match:
        city = city_match.group(1)
        town = city_match.group(2).strip()
    else:
        city_match = re.match(r"^(.+?(?:市|区|町|村|郡))(.*)$", rest)
        if city_match:
            city = city_match.group(1)
            town = city_match.group(2).strip()
        else:
            city = rest
            town = ""

    if not town or town in ("以下に掲載がない場合", "その他"):
        town = None
    return prefecture, city, town if town else None


def search_zipcode(csv_path: Path, prefecture: str, city: str, town: str | None) -> str | None:
    """CSVから該当する郵便番号を検索する。"""
    results = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 9:
                continue
            zipcode = row[2].strip().strip('"')
            pref_val = row[6].strip('"')
            city_val = row[7].strip('"')
            town_val = row[8].strip('"')

            if pref_val != prefecture:
                continue
            if city not in city_val and city_val not in city:
                continue
            if town:
                if town_val != "以下に掲載がない場合" and (town in town_val or town_val.startswith(town)):
                    results.append((zipcode, town_val))
            else:
                results.append((zipcode, town_val))

    if results:
        results.sort(key=lambda x: (len(x[1]), x[0]))
        return results[0][0]
    return None


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: zipcode_from_address.py <住所>", file=sys.stderr)
        return 1

    address = " ".join(sys.argv[1:])
    if not address.strip():
        print("", file=sys.stderr)
        return 1

    try:
        csv_path = ensure_data()
    except Exception as e:
        print(f"データの取得に失敗しました: {e}", file=sys.stderr)
        return 1

    prefecture, city, town = parse_address(address)
    if not prefecture:
        print("", file=sys.stderr)
        return 1

    zipcode = search_zipcode(csv_path, prefecture, city, town)
    if zipcode:
        print(zipcode)
        return 0
    else:
        print("", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
