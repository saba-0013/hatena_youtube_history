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

    files_ = dbx.files_list_folder(path=Settings.FOLDER_PATH).entries
    latest_datetime = max(list(map(lambda x: x.client_modified, files_)))
    print(latest_datetime)

    latest_file_path = list(filter(lambda x: x.client_modified==latest_datetime, files_))[0].path_display
    print(latest_file_path)

    dbx.files_download_to_file(download_path=Settings.DOWNLOAD_PATH, path=latest_file_path)

    with ZipFile(Settings.DOWNLOAD_PATH) as myzip:
        myzip.extractall(Settings.UNZIP_PATH)
    
    return None

# TODO:jinjaとかで作る
def generate_history_html(contents):

    # ヘッダー：tailwind読み込みとタイトル
    # メインコンテンツ：動画サムネgrid
    # サイドコンテンツ：追従動画タイトル/リンクテーブル

    # generate HTML
    doc_header = """
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <div class="text-3xl text-center m-4">
        <p>{TITLE_RANGE}見た動画</p>
    </div>
    """.format(TITLE_RANGE=TITLE_RANGE)

    doc_contents = ""
    docs_ = [doc_header, doc_contents]

    # ページ上に表示する以下2つを生成
    # 1. ページ左サイドに表示するタイトル/リンクのテーブル
    # 2. ページメインに表示するタイトル/リンク/サムネのコンテンツ羅列
    top_open_tag = """<div class="grid grid-cols-5">"""
    div_close_tag = """</div>"""
    docs_.append(top_open_tag)
    
    main_objects = []
    main_open_tag = """<div class="grid grid-cols-2 col-span-3 divide-y divide-black">"""
    main_objects.append(main_open_tag)
    table_objects = []
    table_header = """<div class="h-120 col-span-2 overflow-auto p-4 m-4">
        <table class="table-auto">
            <thead>
                <th class="sticky top-0 border-b pb-4"><p class="text-left">押すとサムネに飛ぶよ</p></th>
            </thead>
            <tbody>
        """
    table_close_tag = """</tbody></table></div>"""
        
    table_objects.append(table_header)
    for i in contents:
        main_obj = """
            <div class="m-4 p-4">
                <p id="{video_id}" class="text-sm"><strong>{title} / {channel}</strong></p>
                <a href="{url}" class="text-blue-600"> {url} </a>
                <img src="https://img.youtube.com/vi/{video_id}/sddefault.jpg" alt="">
            </div>
        """.format(title=i["title"], channel=i["channel"], url=i["titleUrl"], video_id=i["video_id"], )
        
        # table
        table_obj = """
            <tr class="border-b"><td><a href="#{video_id}"><p class="truncate pb-4">{title} / {channel}</p></a></td></tr>
        """.format(title=i["title"], channel=i["channel"], video_id=i["video_id"])

        main_objects.append(main_obj)
        table_objects.append(table_obj)
    main_objects.append(div_close_tag)
    table_objects.append(table_close_tag)
    docs_.extend(table_objects)
    docs_.extend(main_objects)

    docs_.append(div_close_tag)
    content_html = "".join(docs_)

    with open(Settings.HTML_PATH / f"{TITLE_RANGE}.html", mode="w") as f:
        f.write(content_html)
    return content_html

def generate_history_contents():

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



title = f"Youtubeで見た動画 {TITLE_RANGE}"
dbx = dropbox.Dropbox(ACCESS_TOKEN)
download_latest_zip(dbx)
c = generate_history_contents()
html_ = generate_history_html(c)
# res = post_hatena_entry(title, c)
# print(res)
