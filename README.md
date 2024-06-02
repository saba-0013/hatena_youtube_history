# hatena_youtube_history

## WHAT
Youtubeの視聴履歴を自動的にはてなブログに投稿する
手順：

- 履歴データのjsonをdropboxにエクスポート

※視聴履歴のデータエクスポート自体は自動化していないので、この手順だけブラウザ上で[URL](https://support.google.com/accounts/answer/3024190?hl=ja)から取得する（YoutubeAPIにWatchHistoryを取得する術がない、Google Takeoutの自動化は出来るか不明 + まぁ出来るんだろうけど認証だるそうだから手でやっている。楽な方法あったら教えてください）

こっから下はmain.py
- dropboxAPIでローカルへdownload
- 整形してはてブ記事のhtmlに変換
- hatenaAPIで自動投稿


## WHY
Q: なぜ？
A: 過去の自分のYoutube視聴履歴は見れた方が嬉しいから