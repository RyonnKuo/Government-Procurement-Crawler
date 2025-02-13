# 載入套件
import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urlparse, parse_qs
import pandas as pd
from datetime import datetime

# 讓使用者輸入西元年月日
try:
    ispublish_input = input("是否查詢已發布公告？(y/n): ").strip().lower()
    publish_str = 'readPublish' if ispublish_input == 'y' else 'readUnPublish'
    year = int(input("請輸入西元年 (例如 2025): "))
    month = int(input("請輸入月份 (1-12): "))    
    day = int(input("請輸入日期 (1-31): "))

    # 驗證日期
    if year < 1911:
        raise ValueError("西元年須大於 1911！")
    if not (1 <= month <= 12):
        raise ValueError("月份須介於 1 到 12 之間！")
    if not (1 <= day <= 31):
        raise ValueError("日期須介於 1 到 31 之間！")

except ValueError as e:
    print(f"❌ 輸入錯誤: {e}")
    exit(1)  # 直接結束程式

# 轉換成民國年月日
roc_year = year - 1911  # 民國年 = 西元年 - 1911
roc_date = f"{roc_year:03d}年{month:02d}月{day:02d}日"
encoded_date = urllib.parse.quote(roc_date)

# 目標網址
url = f"https://web.pcc.gov.tw/prkms/tender/common/noticeDate/{publish_str}?dateStr={encoded_date}"
# sub page url basic
base_url_publish = 'https://web.pcc.gov.tw/prkms/tender/common/noticeDate/redirectPublic?'
base_url_unpublish = 'https://web.pcc.gov.tw/tps/QueryTender/query/searchTenderDetail?'

# 發送 GET 請求
response = requests.get(url)
response.encoding = "utf-8"  # 設定編碼，避免亂碼

# 確保請求成功
if response.status_code == 200:
    
    print(f"成功取得網頁，狀態碼: {response.status_code}")
    
    # 解析 HTML
    soup = BeautifulSoup(response.text, "html.parser")
    data = []
        
    if publish_str == 'readPublish':
        # 找到所有公開招標公告 = 找到<a></a>這種tag中 class="tenderLinkPublish"的
        tenders = soup.find_all("a", class_="tenderLinkPublish")
        # 確保有找到招標公告
        if not tenders:
            print("沒有找到任何招標公告，請確認日期是否正確或網址是否有效。")
            exit(1)
        
        for tender in tenders:
            title = tender.text.strip()
            raw_href = tender["href"]  # 取得原始 XML 連結
            # 轉換成完整的轉址 URL
            date_str = f"{year}{month:02d}{day:02d}"  # 轉換成 YYYYMMDD
            full_redirect_url = f"{base_url_publish}ds={date_str}&fn={raw_href}"
            # 儲存到數據列表
            data.append([title, full_redirect_url])
    else:
         # 找到所有非公開招標公告 = 找到<a></a>這種tag中 class="tenderLinkUnPublish"的
        tenders = soup.find_all("a", class_="tenderLinkUnPublish")
        # 確保有找到非招標公告
        if not tenders:
            print("沒有找到任何招標公告，請確認日期是否正確或網址是否有效。")
            exit(1)
        for tender in tenders:
            title = tender.text.strip()
            raw_href = tender["href"]
            # 提取 pk 值
            match = re.search(r"([^.]+)$", raw_href)
            pk_value = match.group(1) if match else ""
            full_redirect_url = f"{base_url_unpublish}pkPmsMain={pk_value}"
            data.append([title, full_redirect_url])

    # 建立 DataFrame
    df = pd.DataFrame(data, columns=["title", "link"])

    # 取得當前時間（確保檔案唯一）
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M")  # 2025-02-10_17-23
    # 設定檔案名稱
    filename = f"{publish_str}_{year}-{month:02d}-{day:02d}_{timestamp}.csv"
    # 存成 CSV 檔案
    df.to_csv(filename, index=False, encoding="utf-8-sig")

    print("爬取成功，已儲存為 data.csv")

else:
    print(f"無法獲取網頁，狀態碼: {response.status_code}，請檢查網址或網絡連線")
