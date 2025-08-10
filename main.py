import base64
import json
import urllib.request
from datetime import datetime
from xml.sax.saxutils import escape
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import dropbox
import pandas as pd

from base import Envs, Settings
from html_generator import generate_history_html, generate_index_html

BASE_URL = f"https://blog.hatena.ne.jp/{Envs.HATENA_ID}/{Envs.BLOG_DOMAIN}/atom"
# NOTE: "subtitles"はdict in dictなためdfに入れる前に分解して投稿チャンネル名のみ取得する
OUTPUT_KEYS = ["title", "titleUrl", "time", "subtitles"]
TITLE_RANGE = f"{Settings.LOWER_LIMIT}~{Settings.UPPER_LIMIT}"

# generate_auth
rdbx = dropbox.Dropbox(
    oauth2_refresh_token=Envs.REFRESH_TOKEN,
    app_key=Envs.APP_KEY,
    app_secret=Envs.APP_SECRET
)
rdbx.users_get_current_account()
ACCESS_TOKEN = rdbx._oauth2_access_token


def download_latest_zip(dbx):
    # Googleデータエクスポート経由でdropboxに入ってきたzipの最新データのみ取得、解凍してlatest_file/に配置

    files_ = [i for i in dbx.files_list_folder(path=Settings.FOLDER_PATH).entries if i.path_lower.endswith("-1-001.zip")]
    latest_datetime = max(list(map(lambda x: x.client_modified, files_)))
    print(latest_datetime)

    latest_file_path = list(filter(lambda x: x.client_modified==latest_datetime, files_))[0].path_display
    print(latest_file_path)

    dbx.files_download_to_file(download_path=Settings.DOWNLOAD_PATH, path=latest_file_path)

    with ZipFile(Settings.DOWNLOAD_PATH) as myzip:
        myzip.extractall(Settings.UNZIP_PATH)
    
    return None

def generate_history_contents():
    # history/で表示するhtmlとして整形するためにjsonほぐしてdf -> dictにしておく

    with open(Settings.JSON_PATH, "r") as f:
        history_ = json.load(f)
    # NOTE: Youtube視聴履歴データのtimeはすべてUTCで入っている為JTCに変換して比較する
    latest_c = list(filter(
        lambda x: Settings.UPPER_LIMIT >= (datetime.fromisoformat(x["time"]).astimezone(ZoneInfo("Asia/Tokyo"))).date() >= Settings.LOWER_LIMIT,
        history_
    ))
    print(f"data filtered in {TITLE_RANGE}")

    # 視聴履歴から以下パターンを除外
    # - 広告の再生履歴はtitleUrlが取得できなく不要なため除外
    # - 非公開/削除された動画はsubtitleが取得できないため除外
    latest_history = []
    for c in latest_c:
        # 広告の再生履歴が入ったりするっぽい？確認
        if not c.get("titleUrl", None):
            print(c)
        else:
            tmp_ = {}
            tmp_["title"] = c["title"]
            tmp_["titleUrl"] = c["titleUrl"]
            tmp_["time"] = c["time"]
            subtitles_ = c.get("subtitles", None)
            if subtitles_:
                tmp_["channel"] = c["subtitles"][0]["name"]
                latest_history.append(tmp_)
            # 非公開/削除された動画
            else:
                pass

    for content_ in latest_history:
        content_["title"] = content_["title"].replace("を視聴しました", "")

    # 複数回視聴している動画を最新のみに重複削除
    df_ = pd.DataFrame(latest_history)
    df_ = df_.groupby(["title", "titleUrl", "channel"])["time"].max().reset_index().sort_values("time", ascending=False)
    df_["video_id"] = df_["titleUrl"].apply(lambda x: x.split("watch?v\u003d")[-1])
    contents_ = df_.to_dict(orient="records")

    return contents_

def post_hatena_entry(title, content):
    # 視聴履歴ページ自体はgithub pagesで作成するので、誘導リンクのみの記事を作成する
    title = escape(title)

    # generate HTML
    doc_header = "<h3><strong>今週見た動画</strong></h3>"
    doc_contents = """
    <details>
    <summary>開けば見える</summary>
    """
    docs_ = [doc_header, doc_contents]
    for i in content:
        doc = """

    <p> </p>
    <h4><strong> {title} / {channel}</strong></h4>
    <p> {url} </p>
    """.format(title=i["title"], channel=i["channel"], url=i["titleUrl"])

        docs_.append(doc)
    doc_footer = "</details>"
    docs_.append(doc_footer)
    content_html = "".join(docs_)
    content_html = escape(content_html)

    xml_data = f"""<?xml version="1.0" encoding="utf-8"?>
    <entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
    <title>{title}</title>
    <author><name></name></author>
    <content type="text/html">
        今週： {Settings.PAGES_URL}/history/{TITLE_RANGE}.html
        {content_html}
    </content>
    <category term="見たYoutube" />
    <app:control>
        <app:draft>yes</app:draft>
    </app:control>
    </entry>
    """

    url = BASE_URL + "/entry"
    xml_data = xml_data.encode('utf-8')
    user_pass = base64.b64encode("{user}:{pass_}".format(user=Envs.HATENA_ID, pass_=Envs.API_KEY).encode("utf-8"))
    req = urllib.request.Request(url, xml_data, headers={'Content-Type': 'application/xml', 'Authorization' : 'Basic ' + user_pass.decode("utf-8")})
    response = urllib.request.urlopen(req)

    return response.status


title = f"Youtubeで見た動画 {TITLE_RANGE}"
dbx = dropbox.Dropbox(ACCESS_TOKEN)
download_latest_zip(dbx)
c = generate_history_contents()
history_html = generate_history_html(c)
index_ = generate_index_html()
res = post_hatena_entry(title, c)
print(res)
