# 学認クラウドオンデマンド構築サービスのアプリケーションテンプレート

[国立情報学研究所](https://www.nii.ac.jp/) [クラウド基盤研究開発センター](https://www.nii.ac.jp/research/centers/ccrd/)では、クラウドでのアプリケーション環境構築を支援するため、[「学認クラウドオンデマンド構築サービス」](https://cloud.gakunin.jp/ocs/)を提供しています。
本サービスでは、あらかじめ用意されたテンプレートを指定して実行するだけで、大学・研究機関が契約しているSINETと連携したクラウドに計算資源を確保し、その上で動作するアプリケーション環境のインストールや設定までを用意に行うことができます。
また、いくつかの研究／教育目的のアプリケーションについて、各アプリケーションコミュニティと協力してテンプレートを開発し、情報共有を行っています。

本サイトにおいて、以下のアプリケーションテンプレートを公開いたしました。
各テンプレートは、Jupyter Notebookによりアプリケーションの構築手順が記述されています。
学認クラウドオンデマンド構築サービスで用いている基盤ソフトウェアVCPを用いることを前提としていますが、VCPを利用せずに環境構築する場合のテンプレートも今後公開する予定です。


- [LMSテンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/Moodle)
(VCP SDK v20.04対応、AWS、Azureで動作確認済み)<br>
[Moodle](https://moodle.org/)を用いた学習管理システムを構築します。
本テンプレートでは，パスワード認証の他にShibboleth認証を利用したMoodleの構築手順と，アップデートを行う手順を記載しています。

- [HPCテンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/OpenHPC)
(VCP SDK v20.04対応、AWS、Azureで動作確認済み)<br>
[OpenHPC](https://openhpc.community/)で配布されているパッケージを利用して、クラウド上にHPC環境を構築します。Slurmを利用したジョブスケジューラやSingularityコンテナ利用環境の設定と、構築したHPC環境でのベンチマークプログラムの実行まで行うことができます。

- [講義演習環境テンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/CoursewareHub)
(VCP SDK v20.04対応、AWS、Azureで動作確認済み)<br>
Jupyter Notebook(https://jupyter.org/)を用いた講義演習環境を構築します。
講義演習環境の基盤ソフトウェアには、JupyterHubを講義演習用に国立情報学研究所で拡張した[CoursewareHub](https://github.com/NII-cloud-operation)を用いています。
CoursewareHubでは、教材配布、課題の回答収集、操作履歴の収集等の機能が提供されています。
