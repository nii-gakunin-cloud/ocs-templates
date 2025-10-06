# はじめに
学認クラウドオンデマンド構築サービス（OCS）とOpen OnDemandの概要 (./pdf/OCSとOODの概要-r0.pdf)

# VcpSDKを利用したOpenOnDemandのセットアップ

このテンプレートでは、VcpSDKを利用してOpenOnDemandをインストール・セットアップします。

Open OnDemandは、Web UI経由でジョブ投入を可能にするWebアプリケーションです。Jupyter NotebookなどのようなWebアプリケーションをジョブとして動作させることもサポートしています。

## 概要

[OpenHPC-v2テンプレート](../OpenHPC-v2/)を用いて作成されたOpenHPC/Slurmクラスタに対し、[Open OnDemand](https://openondemand.org/)をインストール・セットアップします。

なお、セットアップにあたっては、OpenHPC-v2テンプレートで作成したgroup_varsとansibleの設定を再利用します。

このテンプレートによる動作確認を実施したクラウド環境は、現在のところmdxのみです。

## システム構成

![](images/ohpc%2Bood.svg)

Open OnDemandは原則としてHPCクラスタのログインノードにインストールするもののため、OpenHPC-v2テンプレートで作成したSlurmクラスタでは、マスターノードにインストールします。

Open OnDemandはOpenHPCと同様、VCノードのBaseコンテナにインストールします。

## 要件

* OpenHPCの構築時と同様、Jupyter NotebookからVcpSDKを用いてVCコントローラにアクセスし、VCノードの制御ができること。
* OpenHPC-v2テンプレートに基いてOpenHPC/Slurmクラスタが構築済みであること。構築の際に作成されたgroup_varsとansibleの設定が残っていること。
* サーバ証明書を用意してHTTPSサーバをセットアップすれば、マスターノードにHTTPSでアクセス可能な状態にあること。Open OnDemandではHTTPSは必須ではないとしているものの、HTTPでは正しく動作しない機能が多く、ほぼ使いものにならない。

## Notebookの使用方法

[このREADMEのあるディレクトリ](./)にあるNotebookを直接開いて使用してください。以下の順に実行することで、Open OnDemandのWeb UIからバッチジョブ実行が可能となります。

1. [010-インストール](./010-%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB.ipynb)
1. [020-フロントエンドのセットアップ](./020-%E3%83%95%E3%83%AD%E3%83%B3%E3%83%88%E3%82%A8%E3%83%B3%E3%83%89%E3%81%AE%E3%82%BB%E3%83%83%E3%83%88%E3%82%A2%E3%83%83%E3%83%97.ipynb)
1. [030-ジョブ実行環境の設定](./030-%E3%82%B8%E3%83%A7%E3%83%96%E5%AE%9F%E8%A1%8C%E7%92%B0%E5%A2%83%E3%81%AE%E8%A8%AD%E5%AE%9A.ipynb)

「[040-ジョブの実行](./040-%E3%82%B8%E3%83%A7%E3%83%96%E3%81%AE%E5%AE%9F%E8%A1%8C.ipynb)」は、Open OnDemandのWeb UIからのバッチジョブ実行方法を示したものです。このNotebookにはコード部分は存在せず、ドキュメントのみです。


「[050-JupyterNotebookのセットアップ](./050-JupyterNotebook%E3%81%AE%E3%82%BB%E3%83%83%E3%83%88%E3%82%A2%E3%83%83%E3%83%97.ipynb)」のNotebookは、Jupyter Notebookサーバをジョブとして実行するための設定を示したものです。通常のバッチジョブを実行するだけであれば、実行する必要はありません。
