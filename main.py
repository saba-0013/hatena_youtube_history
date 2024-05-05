import base64
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile

import dropbox
import pandas as pd

# dropbox
APP_KEY = os.environ["DBAppKey"]
APP_SECRET = os.environ["DBAppSecret"]
REFRESH_TOKEN = os.environ["DBRefreshToken"]

# generate_auth
rdbx = dropbox.Dropbox(
    oauth2_refresh_token=REFRESH_TOKEN,
    app_key=APP_KEY,
    app_secret=APP_SECRET
)
rdbx.users_get_current_account()
ACCESS_TOKEN = rdbx._oauth2_access_token

# settings
FOLDER_PATH = "/apps/google download your data"
DOWNLOAD_PATH = Path("./latest_file/latest.zip")
UNZIP_PATH = Path("./latest_file/latest")

CURRENT_TIMESTAMP = datetime.now(timezone.utc)
CURRENT_DATE = datetime.now().date()
INTERVAL_DATE = 7

# subtitlesはdict in dictなためdfに入れる前に分解して投稿チャンネル名のみ取得する
OUTPUT_KEYS = ["title", "titleUrl", "time", "subtitles"]
JSON_PATH = Path(UNZIP_PATH / "Takeout/YouTube と YouTube Music/履歴/watch-history.json")
HTML_PATH = Path("./contents.html")
# hatena
HATENA_ID = "jobstatus_is_null"
BLOG_DOMAIN = "jobstatus-is-null.hatenablog.com"
API_KEY = os.environ["HatenaApiKey"]
BASE_URL = f"https://blog.hatena.ne.jp/{HATENA_ID}/{BLOG_DOMAIN}/atom"


def download_latest_zip(dbx):

    files_ = dbx.files_list_folder(path=FOLDER_PATH).entries
    latest_datetime = max(list(map(lambda x: x.client_modified, files_)))
    print(latest_datetime)

    latest_file_path = list(filter(lambda x: x.client_modified==latest_datetime, files_))[0].path_display
    print(latest_file_path)

    dbx.files_download_to_file(download_path=DOWNLOAD_PATH, path=latest_file_path)

    with ZipFile(DOWNLOAD_PATH) as myzip:
        myzip.extractall(UNZIP_PATH)
    
    return None

def generate_history_contents():

    with open(JSON_PATH, "r") as f:
        history_ = json.load(f)
    print(CURRENT_TIMESTAMP - timedelta(days=INTERVAL_DATE))
    past_week = CURRENT_TIMESTAMP - timedelta(days=INTERVAL_DATE)
    latest_c = list(filter(lambda x: datetime.fromisoformat(x["time"]) > past_week, history_))

    # 視聴履歴にあるが非公開/削除された動画はsubtitleが取得できないため除外
    latest_history = []
    for c in latest_c:
        tmp_ = {}
        tmp_["title"] = c["title"]
        tmp_["titleUrl"] = c["titleUrl"]
        tmp_["time"] = c["time"]
        subtitles_ = c.get("subtitles", None)
        if subtitles_:
            tmp_["channel"] = c["subtitles"][0]["name"]
            latest_history.append(tmp_)
        else:
            pass

    for content_ in latest_history:
        content_["title"] = content_["title"].replace("を視聴しました", "")

    # 複数回視聴している動画を最新のみに重複削除
    df_ = pd.DataFrame(latest_history)
    df_ = df_.groupby(["title", "titleUrl", "channel"])["time"].max().reset_index().sort_values("time", ascending=False)
    df_["embedUrl"] = df_["titleUrl"].str.replace("watch?v=", "/embed/")
    contents_ = df_.to_dict(orient="records")

    # generate HTML
    doc_header = "<h3><strong>今週見た動画</strong></h3>"
    doc_contents = """
    <p>[:contents]</p>
    """
    docs_ = [doc_header, doc_contents]
    for i in contents_:
        doc = """

    <p> </p>
    <h4><strong> {title} / {channel}</strong></h4>
    <p> {url} </p>
    """.format(title=i["title"], channel=i["channel"], url=i["titleUrl"])

        docs_.append(doc)
    content_html = "".join(docs_)

    with open(HTML_PATH, mode="w") as f:
        f.write(content_html)
    
    return content_html

def post_hatena_entry(title, content):
    title = escape(title)
    content = escape(content)

    xml_data = """<?xml version="1.0" encoding="utf-8"?>
    <entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
    <title>{title}</title>
    <author><name></name></author>
    <content type="text/html">
        {content}
    </content>
    <category term="見たYoutube" />
    <app:control>
        <app:draft>yes</app:draft>
    </app:control>
    </entry>
    """.format(title=title, content=content)

    url = BASE_URL + "/entry"
    xml_data = xml_data.encode('utf-8')
    user_pass = base64.b64encode("{user}:{pass_}".format(user=HATENA_ID, pass_=API_KEY).encode("utf-8"))
    req = urllib.request.Request(url, xml_data, headers={'Content-Type': 'application/xml', 'Authorization' : 'Basic ' + user_pass.decode("utf-8")})
    response = urllib.request.urlopen(req)

    return response.status



title = f"Youtubeで見た動画 ~{CURRENT_DATE}"
dbx = dropbox.Dropbox(ACCESS_TOKEN)
download_latest_zip(dbx)
c = generate_history_contents()
res = post_hatena_entry(title, c)
print(res)
