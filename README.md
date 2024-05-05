# hatena_youtube_history

## WHAT
Youtubeの視聴履歴を自動的にはてなブログに投稿する
手順：

- 履歴データのjsonをdropboxにエクスポート
※視聴履歴のデータエクスポート自体は自動化していないので、この手順だけブラウザ上で[URL](https://support.google.com/accounts/answer/3024190?hl=ja)から取得する（YoutubeAPIにWatchHistoryを取得する術がない、Google Takeoutの自動化は出来るか不明 + 出来ても認証だるそう）

こっから下はmain.py
- dropboxAPIでローカルに取得
- 整形してhtmlに変換
- hatenaAPIで自動投稿


## WHY
なぜ？
なぜ...？