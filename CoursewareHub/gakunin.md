# 学認連携設定ガイド

CoursewareHubにおける学認（GakuNin）連携の詳細設定ガイドです。

## 1. 概要

学認連携により、学認フェデレーション参加機関のユーザがシングルサインオン（SSO）でCoursewareHubにアクセスできます。ユーザID管理が不要で、大規模利用や複数大学での共同講義に適しています。

## 2. 学認連携の方式

CoursewareHubでは以下の２つの学認連携方式を選択できます：

### 2.1. IdP-proxy経由の学認連携（推奨）

**特徴:**

* 自組織で構築するIdP-proxyサーバを経由
* CoursewareHubとIdP-proxyの間はSAMLで連携
* 学認フェデレーションへの直接参加が不要
* IdP-proxy構築の負荷があるが、複数CoursewareHub環境では相対的に運用負荷軽減

**システム構成:**

![IdP-proxy経由の学認連携](notebooks/images/cw-221-01.png)

**適用場面:**

* 学認連携を簡単に導入したい場合
* CoursewareHubを学認SPとして直接登録したくない場合
* 複数のCoursewareHub環境で学認連携を利用したい場合

### 2.2. 直接学認フェデレーション連携

**特徴:**

* CoursewareHub自体を学認SPとして直接登録
* SAML認証を直接処理
* IdP-proxyを経由しない直接的な連携

**システム構成:**

![直接学認フェデレーション連携](notebooks/images/cw-321-01.png)

**適用場面:**

* IdP-proxyを経由させたくない場合
* 機関固有の認証要件がある場合

## 3. 選択指針

| 項目 | IdP-proxy経由 | 直接連携 |
|------|---------------|----------|
| **設定難易度** | 高（IdP-proxy構築含む） | 中 |
| **運用負荷** | 複数環境では相対的に低 | 高 |
| **学認参加申請** | 個別のCoursewareHubは不要<br>IdP-proxyは必要| 必要 |
| **環境数での効率** | 複数環境で有利 | 単一環境向け |
| **推奨度** | ★★★（複数環境時） | ★★ |

**IdP-proxy経由を推奨する理由:**

* 複数CoursewareHub環境での学認連携が効率的
* 学認フェデレーションへの参加申請が不要
* 一度IdP-proxyを構築すれば複数環境で共用可能

## 4. 事前準備

### 4.1. 共通要件

* **NTP設定**: SAML認証では時刻同期が重要
* **DNS設定**: CoursewareHubのFQDNが適切に解決できること
* **SSL証明書**: CoursewareHub用のサーバ証明書

### 4.2. IdP-proxy経由の場合

* **IdP-proxy用SSL証明書**: IdP-proxyサーバ用のサーバ証明書と秘密鍵
* **学認フェデレーション参加申請**: IdP-proxyの学認への申請が必要

### 4.3. 直接連携の場合

* **学認フェデレーション参加申請**: 学認への申請が必要

## 5. 構築手順

### 5.1. IdP-proxy経由での学認連携

基本的なCoursewareHub環境構築後、以下の追加手順を実行します：

#### IdP-proxyの構築

1. [511-VCノード作成-IdP-proxy](notebooks/511-VCノード作成-IdP-proxy.ipynb)
2. [521-IdP-proxyのセットアップ](notebooks/521-IdP-proxyのセットアップ.ipynb)

#### 学認連携の設定

1. [211-学認連携の設定を行う-IdP-proxyを利用する](notebooks/211-学認連携の設定を行う-IdP-proxyを利用する.ipynb)
2. [541-IdP-proxyへauth-proxyのメタデータを登録する](notebooks/541-IdP-proxyへauth-proxyのメタデータを登録する.ipynb)

### 5.2. 直接学認フェデレーション連携

* [311-学認連携の設定を行う-直接学認フェデレーションを利用する](notebooks/311-学認連携の設定を行う-直接学認フェデレーションを利用する.ipynb)
    * SAML認証設定
    * 学認フェデレーション参加申請

## 6. 関連Notebook一覧

### 6.1. IdP-proxy関連

| Notebook | 用途 | 実行タイミング |
|----------|------|----------------|
| [511: VCノード作成--IdP-proxy](notebooks/511-VCノード作成-IdP-proxy.ipynb) | IdP-proxy用ノード作成 | 初期構築時 |
| [521: IdP-proxyセットアップ](notebooks/521-IdP-proxyのセットアップ.ipynb) | IdP-proxy構築 | 初期構築時 |
| [541: メタデータ登録](notebooks/541-IdP-proxyへauth-proxyのメタデータを登録する.ipynb) | メタデータ登録 | 連携設定時 |
| [591: IdP-proxy削除](notebooks/591-IdP-proxyの削除.ipynb) | 環境削除 | 廃止時 |

### 6.2. 学認連携関連

| Notebook | 認証方式 | 用途 |
|----------|----------|------|
| [211: 学認連携--IdP-proxy](notebooks/211-学認連携の設定を行う-IdP-proxyを利用する.ipynb) | IdP-proxy経由 | 推奨方式での連携設定 |
| [311: 学認連携--直接連携](notebooks/311-学認連携の設定を行う-直接学認フェデレーションを利用する.ipynb) | 直接SP登録 | 高度な設定での連携 |

## 7. 参考資料

* [学認フェデレーション公式サイト](https://www.gakunin.jp/)
* [IdP-Proxy](https://github.com/NII-cloud-operation/CoursewareHub-LC_idp-proxy)
