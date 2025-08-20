# plugins ディレクトリについて

このディレクトリには、CoursewareHub環境のlc_wrapperログ解析に特化したカスタムプラグインが含まれています。これらのプラグインは、Fluentdとnotebook実行状況の可視化システムで使用されます。

## 主な内容

- `fluent-plugin-lc-wrapper/`  
  LC_wrapperログ解析用パーサプラグイン。Jupyter-LC_wrapperが出力するログを構造化データに変換します。

- `fluent-plugin-attach-file/`  
  ファイル添付用フィルタプラグイン。ログレコードにファイル内容を添付し、詳細な解析を可能にします。

- `fluent-plugin-related-info/`  
  関連情報付加用フィルタプラグイン。外部辞書ファイル（CSV/TSV/JSON）を参照してレコードに情報を付加します。

- `memeid-extractor/`  
  MEME ID抽出・処理用Pythonパッケージ。notebook実行状況の追跡と可視化に使用されます。

## 備考

各プラグインの詳細な仕様、インストール方法、使用方法については、各サブディレクトリのREADME.mdを参照してください。
