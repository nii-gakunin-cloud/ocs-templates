# 学認クラウドオンデマンド構築サービスのアプリケーションテンプレート

[国立情報学研究所](https://www.nii.ac.jp/) [クラウド基盤研究開発センター](https://www.nii.ac.jp/research/centers/ccrd/)では、クラウドでのアプリケーション環境構築を支援するため、[「学認クラウドオンデマンド構築サービス」](https://cloud.gakunin.jp/ocs/)を提供しています。
本サービスでは、あらかじめ用意されたテンプレートを指定して実行するだけで、大学・研究機関が契約しているSINETと連携したクラウドに計算資源を確保し、その上で動作するアプリケーション環境のインストールや設定までを用意に行うことができます。
また、いくつかの研究／教育目的のアプリケーションについて、各アプリケーションコミュニティと協力してテンプレートを開発し、情報共有を行っています。

本サイトにおいて、以下のアプリケーションテンプレートを公開いたしました。
各テンプレートは、Jupyter Notebookによりアプリケーションの構築手順が記述されています。
学認クラウドオンデマンド構築サービスで用いている基盤ソフトウェアVCPを用いることを前提としていますが、VCPを利用せずに環境構築する場合のテンプレートも一部公開しています。

- [LMSテンプレート簡易構成版](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/Moodle-Simple)
(VCP SDK v22.04以降対応 (AWS、Azureで動作確認済み)、AWS対応、Azure対応)<br>
[Moodle](https://moodle.org/)を用いた学習管理システムを構築します。
本テンプレートでは、[LMSテンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/Moodle)
よりも機能を絞ったシンプルな構成でクラウド上にMoodleを立ち上げる手順を記載しており、手動アカウントかLDAP連携を用いた短期的な利用を想定しています。
Shibboleth等のSSO連携や、長期利用のためのアップデート方法については、本構成を元に各機関の事情に合わせてカスタマイズしてご利用いただくことを想定しています。
本テンプレートでは、VCPを利用せずにAWSまたはAzureに直接LMS環境を構築する手順も合わせて公開しています。

- [HPCテンプレート v3](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/OpenHPC-v3)
(VCP SDK v22.04対応 (AWS、Azureで動作確認済み))<br>
[OpenHPC](https://openhpc.community/) v3.xで配布されているパッケージを利用して、クラウド上にHPC環境を構築します。Slurmを利用したジョブスケジューラやSingularityコンテナ利用環境の設定、GPUノードの設定と、構築したHPC環境でのベンチマークプログラムの実行やNVIDIA社の[NGCカタログ](https://www.nvidia.com/ja-jp/gpu-cloud/containers/)のコンテナ実行まで行うことができます。
ベースコンテナにはRocky Linux v9.xを利用しています．

- [HPCテンプレート v2](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/OpenHPC-v2)
(VCP SDK v22.04対応 (AWS、Azure、Oracle Cloud Infrastructure、mdxで動作確認済み))<br>
[OpenHPC](https://openhpc.community/) v2.xで配布されているパッケージを利用して、クラウド上にHPC環境を構築します。Slurmを利用したジョブスケジューラやSingularityコンテナ利用環境の設定、GPUノードの設定と、構築したHPC環境でのベンチマークプログラムの実行やNVIDIA社の[NGCカタログ](https://www.nvidia.com/ja-jp/gpu-cloud/containers/)のコンテナ実行まで行うことができます。
ベースコンテナにはRocky Linux v8.xを利用しています．

- [Open OnDemandテンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/OpenOnDemand)
(VCP SDK v22.04以降対応 (mdxで動作確認済み))<br>
HPCテンプレートv2で構築したOpenHPC環境上にOpen OnDemand環境を構築する


- [計算資源補完テンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/HybridCloud)
(VCP SDK v22.04以降対応 (AWS、Azureで動作確認済み))<br>
オンプレミスのバッチ型計算機システムの計算ノードが不足したとき、クラウド上にオンプレミスシステムと同様のソフトウェア構成を持つ計算ノードを立ち上げ、バッチシステムに組み込むクラウドバースト機能をVCPで実現するテンプレートです。Torque等クラウドに対応していないバッチシステムでも、簡単なプラグインを作成することでクラウドバーストを実現できます。なお、本テンプレートはipynb形式ではなく、Pythonならびにbashスクリプトで記述されています。

- [手書き文字認識システム構築テンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/OpenHPC-ML-Example)
(VCP SDK v22.04対応 (AWS、Azureで動作確認済み))<br>
Open HPC v2テンプレートをベースにGPU ベースの学習システム（Tensorflowを使用）の構築とCPUベースの認識システム（独自仕様）の構築を行い、フロントエンドとしてJupyterNotebook上に手書き数字認識システムを動作させる。

- [講義演習環境テンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/CoursewareHub)
(VCP SDK v22.04対応 (AWS、Azure、mdxで動作確認済み))<br>
[Jupyter Notebook](https://jupyter.org/)を用いた講義演習環境を構築します。
講義演習環境の基盤ソフトウェアには、JupyterHub v3.xを講義演習用に国立情報学研究所で拡張した[CoursewareHub](https://github.com/NII-cloud-operation)を用いています。
CoursewareHubでは、教材配布、課題の回答収集、操作履歴の収集等の機能が提供されています。

- [軽量Python実習環境構築テンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/TheLittlestJupyterHub)
(VCP SDK v22.04対応 (AWS、Azure、mdxで動作確認済み))<br>
Pythonによるプログラムの共同開発や講義演習などを行うのに適したJupyterHubの中で小規模グループ用である「The Littlest JupyterHub」の環境構築をおこなう。

- [MCJ-CloudHub環境構築テンプレート](https://github.com/nii-gakunin-cloud/mcj-cloudhub)
複数科目で共同・同時利用可能なWeb型プログラミング演習システムであるMCJ-CloudHubの環境構築・運用を行う。
MCJ-CloudHubは、Web型プログラミング演習環境としてJupyterHubを、課題の配布・回収・採点ツールとしてnbgraderを採用し、複数科目で共同・同時利用可能とするために独自の改修・設定を行っている。 


なお，以下のテンプレートは保守を終了しました．代替となる上記テンプレートの利用をおすすめします．

- [LMSテンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/Moodle)
(VCP SDK v22.04以降対応 (AWS、Azureで動作確認済み))<br>
[Moodle](https://moodle.org/)を用いた学習管理システムを構築します。
本テンプレートでは，パスワード認証の他にShibboleth認証を利用したMoodleの構築手順と，アップデートを行う手順を記載しています。<br>
（参考文献） Moodle運用におけるDocker及びJupyter Notebookの活用。浜元 信州、横山 重俊、竹房 あつ子、合田 憲人、桑田 喜隆、石坂 徹。[日本ムードル協会全国大会2018発表論文集](https://moodlejapan.org/mod/resource/view.php?id=1474)、pp. 6-12、2018年10月。

- [HPCテンプレート v1](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/OpenHPC-v1)
(VCP SDK v22.04以降対応 (AWS、Azureで動作確認済み))<br>
[OpenHPC](https://openhpc.community/) v1.xで配布されているパッケージを利用して、クラウド上にHPC環境を構築します。Slurmを利用したジョブスケジューラやSingularityコンテナ利用環境の設定と、構築したHPC環境でのベンチマークプログラムの実行まで行うことができます。

- [JupyterHub v1.xベース講義演習環境テンプレート](https://github.com/nii-gakunin-cloud/ocs-templates/tree/master/CoursewareHub-not-recommended)
(VCP SDK v22.04対応 (AWS、Azure、mdxで動作確認済み))<br>
[Jupyter Notebook](https://jupyter.org/)を用いた講義演習環境を構築します。
講義演習環境の基盤ソフトウェアには、JupyterHub v1.xを講義演習用に国立情報学研究所で拡張した[CoursewareHub](https://github.com/NII-cloud-operation)を用いています。
