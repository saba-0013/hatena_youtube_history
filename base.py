import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass
class Envs:

    # dropbox
    # ref: https://dropbox-sdk-python.readthedocs.io/en/latest/
    # ref: https://github.com/dropbox/dropbox-sdk-python/
    APP_KEY = os.environ["DBAppKey"]
    APP_SECRET = os.environ["DBAppSecret"]
    REFRESH_TOKEN = os.environ["DBRefreshToken"]
    
    # hatena
    # ref: https://developer.hatena.ne.jp/ja/documents/blog/apis/atom/
    HATENA_ID = os.environ["HatenaId"]
    BLOG_DOMAIN = os.environ["HatenaDomain"]
    API_KEY = os.environ["HatenaApiKey"]

@dataclass
class Settings:

    # dirs

    # dropbox内exportデータ出力先
    FOLDER_PATH = "/apps/google download your data"

    # localへ落としてきた履歴データ保存先
    DOWNLOAD_PATH = Path("./latest_file/latest.zip")
    UNZIP_PATH = Path("./latest_file/latest")
    JSON_PATH = Path(UNZIP_PATH / "Takeout/YouTube と YouTube Music/履歴/watch-history.json")

    # 生成htmlデータ出力先
    HTML_PATH = Path("./contents.html")

    # times
    CURRENT_TIMESTAMP = datetime.now(ZoneInfo("Asia/Tokyo"))
    INTERVAL_DATE = 7
    UPPER_LIMIT = CURRENT_TIMESTAMP.date() - timedelta(days=1)
    LOWER_LIMIT = CURRENT_TIMESTAMP.date() - timedelta(days=INTERVAL_DATE)