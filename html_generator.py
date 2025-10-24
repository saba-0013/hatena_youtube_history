from base import Settings

TITLE_RANGE = f"{Settings.LOWER_LIMIT}~{Settings.UPPER_LIMIT}"


def generate_index_html():
    # トップにタイトルとliでperiod別リンクがついてる奴
    # /history/下ファイル取得
    listing = Settings.HISTORY_PATH
    listings = []
    
    doc_header = """
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <div class="text-3xl text-center m-4">
        <p>youtubeで見た動画たち</p>
    </div>
    """

    listing_open = """
    <div class="p-8"><ul class="text-blue-600">
    """
    listing_close = """
    </ul></div>
    """
    docs_ = [doc_header, listing_open]

    for period in sorted(listing.iterdir(), reverse=True):
        print(period)
        listing_item = f"""
        <li><a href="history/{period.name}">{period.stem}</a></li>       
        """
        docs_.append(listing_item)

    docs_.append(listing_close)
    content_html = "".join(docs_)
    with open(f"{Settings.INDEX_PATH}/index.html", mode="w") as f:
        f.write(content_html)
    return None

def generate_history_html(contents):

    # ヘッダー：tailwind読み込みとタイトル
    # メインコンテンツ：動画サムネgrid

    # generate HTML
    doc_header = """
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <div class="bg-gray-700">
        <div class="bg-gray-800 sticky top-0 flex">
            <a href="../index.html" class="p-3"><img src="../home.svg" alt=""></a>
            <p class="text-2xl text-center p-3 text-white flex-1">{TITLE_RANGE}見た動画</p>
        </div>
    """.format(TITLE_RANGE=TITLE_RANGE)

    doc_contents = ""
    docs_ = [doc_header, doc_contents]

    # ページ上に表示する以下2つを生成
    # 2. ページメインに表示するタイトル/リンク/サムネのコンテンツ羅列
    top_open_tag = """<div class="grid lg:grid-cols-3 grid-cols-2">"""
    div_close_tag = """</div>"""
    docs_.append(top_open_tag)
    
    main_objects = []
    main_open_tag = """<div class="lg:m-8 grid lg:grid-cols-3 grid-cols-2 lg:col-span-3 col-span-2 divide-y divide-white">"""
    main_objects.append(main_open_tag)
    for i in contents:
        main_obj = """
            <div class="m-4 p-4">
                <p id="{video_id}" class="text-sm text-white"><strong>{title} / {channel}</strong></p>
                <a href="{url}" class="text-blue-600"> {url} </a>
                <img src="https://img.youtube.com/vi/{video_id}/sddefault.jpg" alt="" loading="lazy">
            </div>
        """.format(title=i["title"], channel=i["channel"], url=i["titleUrl"], video_id=i["video_id"], )
        
        # table
        table_obj = """
            <tr class="border-b"><td><a href="#{video_id}"><p class="truncate pb-4">{title} / {channel}</p></a></td></tr>
        """.format(title=i["title"], channel=i["channel"], video_id=i["video_id"])

        main_objects.append(main_obj)
    main_objects.append(div_close_tag)
    docs_.extend(main_objects)

    docs_.append(div_close_tag)
    docs_.append(div_close_tag)
    content_html = "".join(docs_)

    with open(Settings.HISTORY_PATH / f"{TITLE_RANGE}.html", mode="w") as f:
        f.write(content_html)
    return None