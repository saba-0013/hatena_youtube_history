import base64
import json
import urllib.parse
import urllib.request
from datetime import datetime
from xml.sax.saxutils import escape
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import dropbox
import pandas as pd

from base import Envs, Settings

# subtitlesはdict in dictなためdfに入れる前に分解して投稿チャンネル名のみ取得する
OUTPUT_KEYS = ["title", "titleUrl", "time", "subtitles"]
BASE_URL = f"https://blog.hatena.ne.jp/{Envs.HATENA_ID}/{Envs.BLOG_DOMAIN}/atom"


# generate_auth
rdbx = dropbox.Dropbox(
    oauth2_refresh_token=Envs.REFRESH_TOKEN,
    app_key=Envs.APP_KEY,
    app_secret=Envs.APP_SECRET
)
rdbx.users_get_current_account()
ACCESS_TOKEN = rdbx._oauth2_access_token


def download_latest_zip(dbx):

    files_ = dbx.files_list_folder(path=Settings.FOLDER_PATH).entries
    latest_datetime = max(list(map(lambda x: x.client_modified, files_)))
    print(latest_datetime)

    latest_file_path = list(filter(lambda x: x.client_modified==latest_datetime, files_))[0].path_display
    print(latest_file_path)

    dbx.files_download_to_file(download_path=Settings.DOWNLOAD_PATH, path=latest_file_path)

    with ZipFile(Settings.DOWNLOAD_PATH) as myzip:
        myzip.extractall(Settings.UNZIP_PATH)
    
    return None

def generate_history_contents():

    with open(Settings.JSON_PATH, "r") as f:
        history_ = json.load(f)
    # NOTE: Youtube視聴履歴データのtimeはすべてUTCで入っている為JTCに変換して比較する
    latest_c = list(filter(
        lambda x: Settings.UPPER_LIMIT >= (datetime.fromisoformat(x["time"]).astimezone(ZoneInfo("Asia/Tokyo"))).date() >= Settings.LOWER_LIMIT,
        history_
    ))
    print(f"data filtered in {Settings.LOWER_LIMIT} ~ {Settings.UPPER_LIMIT}")

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
    df_.to_csv("test.csv", index=False)
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

    with open(Settings.HTML_PATH, mode="w") as f:
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
    user_pass = base64.b64encode("{user}:{pass_}".format(user=Envs.HATENA_ID, pass_=Envs.API_KEY).encode("utf-8"))
    req = urllib.request.Request(url, xml_data, headers={'Content-Type': 'application/xml', 'Authorization' : 'Basic ' + user_pass.decode("utf-8")})
    response = urllib.request.urlopen(req)

    return response.status



title = f"Youtubeで見た動画 {Settings.LOWER_LIMIT}~{Settings.UPPER_LIMIT}"
dbx = dropbox.Dropbox(ACCESS_TOKEN)
download_latest_zip(dbx)
c = generate_history_contents()
res = post_hatena_entry(title, c)
print(res)
