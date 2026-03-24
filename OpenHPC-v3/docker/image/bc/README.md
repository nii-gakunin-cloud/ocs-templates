# OpenHPC-v3 ベースコンテナイメージ

このディレクトリには、OpenHPC-v3環境を構成するベースコンテナイメージのDockerfileと関連ファイルが含まれています。

## 概要

- **OpenHPCバージョン**: 3.4
- **Slurmバージョン**: 24.11.5
- **ベースOS**: Rocky Linux 9

## イメージ構成

### master/

マスターノード用のコンテナイメージです。

**主な機能**:
- Slurm slurmctld（ジョブスケジューラ）
- NFS server（/exportsの共有）
- Munge認証サービス
- OpenHPC開発ツール（コンパイラ、MPI、ライブラリ）

**主要コンポーネント**:
- `Dockerfile`: マスターノードイメージの定義
- `etc/vcp/rc.d/20-slurm.sh`: Slurm設定の初期化スクリプト
- `etc/vcp/rc.d/templates/slurm.conf.j2`: Slurm設定テンプレート
- `etc/slurm/gres.conf`: GPU Resource設定（AutoDetect=nvidia）

**Dockerメタデータ**:
```dockerfile
LABEL jp.ac.nii.vcloud.ocs.openhpc.slurm_conf_template="2.0"
LABEL jp.ac.nii.vcloud.ocs.openhpc.partition_support="multi"
```

### compute/

計算ノード用のコンテナイメージです。

**主な機能**:
- Slurm slurmd（計算ノードデーモン）
- Munge認証サービス
- OpenHPC実行環境（MPI、ライブラリ）
- Apptainer（コンテナ実行環境）

**設定の取得**:
- Slurm configless modeにより、マスターノードから自動的に設定を取得
- slurmd起動時にslurmctldから最新の設定をダウンロード

### compute-gpu/

GPU対応計算ノード用のコンテナイメージです。

**主な機能**:
- compute/の全機能
- NVIDIA GPU対応
- GPU Resource（GRES）管理

**追加要件**:
- ホスト側にNVIDIA Dockerランタイムが必要
- 適切なGPUドライバがホストにインストール済みであること

## ビルド方法

### 前提条件

- Docker 23.0以上
- Docker Buildx（Docker 23.0以降はデフォルトで含まれる）

### ビルドコマンド

```bash
# すべてのイメージをビルド
cd OpenHPC-v3/docker/image/bc
docker buildx bake

# 特定のイメージのみビルド
docker buildx bake master
docker buildx bake compute
docker buildx bake compute-gpu
```

### イメージタグ

ビルド時に以下の2種類のタグが生成されます：

**基本タグ**（最新ビルドを指す）:
- `harbor.vcloud.nii.ac.jp/vcp/openhpc:master-3.4-multi`
- `harbor.vcloud.nii.ac.jp/vcp/openhpc:compute-3.4-multi`
- `harbor.vcloud.nii.ac.jp/vcp/openhpc:compute-gpu-3.4-multi`

**日付付きタグ**（特定ビルドを保持）:
- `harbor.vcloud.nii.ac.jp/vcp/openhpc:master-3.4-multi-YYYYMMDD`
- `harbor.vcloud.nii.ac.jp/vcp/openhpc:compute-3.4-multi-YYYYMMDD`
- `harbor.vcloud.nii.ac.jp/vcp/openhpc:compute-gpu-3.4-multi-YYYYMMDD`

日付付きタグは特定バージョンの再現性を確保するために使用します。

## 環境変数

### マスターノード（必須）

| 環境変数 | 説明 | 例 |
|---------|------|-----|
| `MUNGE_KEY` | Munge認証キー（base64エンコード） | `xxx...` |
| `CLUSTER` | Slurmクラスタ名 | `OpenHPC` |
| `PRIVATE_IP` | ノードのプライベートIPアドレス（VCPプラットフォームが自動設定） | `172.30.2.100` |

**注意：** `MaxNodeCount` はAnsibleでFeature設定（各Featureの `ip_addresses` の合計）に基づき自動計算されます。

### マスターノード（オプション）

| 環境変数 | 説明 | 例 |
|---------|------|-----|
| `DNS_DOMAIN` | クラスタ内部ドメイン名（デフォルト: `ohpc.internal`） | `ohpc.internal` |
| `DNS_FORWARDERS` | 外部DNS問い合わせ先（カンマ区切り、デフォルト: `8.8.8.8,8.8.4.4`） | `8.8.8.8,8.8.4.4` または `1.1.1.1,1.0.0.1` |
| `NFS_DEV` | NFSディスクのデバイス名 | `/dev/xvdf` |
| `ENABLE_NSS_SLURM` | NSS Slurmの有効化 | `1` |

**注意：** Feature/Partition設定（MaxNodeCount、GresTypes、NodeSet、PartitionName）はAnsibleでpost-deployment時に追加されます。

### 計算ノード（必須）

| 環境変数 | 説明 | 例 |
|---------|------|-----|
| `MUNGE_KEY` | Munge認証キー（マスターと同じ） | `xxx...` |
| `MASTER_HOSTNAME` | マスターノードのホスト名 | `master` |
| `CLUSTER` | Slurmクラスタ名（マスターと同じ） | `OpenHPC` |
| `FEATURE` | ノードのFeature名 | `aws-medium` |
| `PRIVATE_IP` | ノードのプライベートIPアドレス（VCPプラットフォームが自動設定） | `172.30.2.101` |

**ホスト名の決定:**
- 計算ノードのホスト名はAnsibleが管理する `/opt/ohpc/pub/etc/hosts.ohpc` から取得されます
- 各Featureの `hostname_template` に基づきAnsibleがホスト名を生成し、IPアドレスとの対応をhostsファイルに書き込みます
- 計算ノード起動時に `setup-hostname.sh` が `PRIVATE_IP` でhostsファイルを検索し、対応するホスト名を設定します
- テンプレート例: `c{}`（c1, c2, ...）、`c{:02}`（c01, c02, ...）、`gpu{:02}`（gpu01, gpu02, ...）

### 計算ノード（オプション）

| 環境変数 | 説明 | 例 |
|---------|------|-----|
| `GPUS` | GPU数（slurmdのGRES宣言に使用） | `1` |
| `ENABLE_NSS_SLURM` | NSS Slurmの有効化 | `1` |
| `OPTIONAL_NFS_FSTAB_BASE64` | 追加NFSマウント（base64エンコード） | `xxx...` |

## Slurm Configless Mode

Slurm 24.11以降のconfigless modeを使用しています。

**利点**:
- 計算ノードは slurm.conf を持たず、マスターノードから自動取得
- 設定変更時は `scontrol reconfigure` のみで全ノードに反映
- 設定の一元管理が可能

**動作**:
1. マスターノード：基本設定のみの `slurm.conf` を起動時に生成
2. Ansible：Feature/Partition設定（MaxNodeCount、GresTypes、NodeSet、PartitionName）を追加
3. 計算ノード：起動時にslurmctldから完全な設定をダウンロード
4. 設定変更：マスターで `scontrol reconfigure` → 全計算ノードに自動配布

**注意**:
- `gres.conf` はマスターノードのイメージに同梱されており、configless modeで計算ノードに自動配布されます

## Dynamic Nodes

Slurm Dynamic Nodesを使用して、計算ノードを動的に追加・削除できます。

**設定**:
- `MaxNodeCount` はAnsibleでFeature設定に基づき計算・設定されます
- 各Featureの最大ノード数（`ip_addresses` の数）の合計が `MaxNodeCount` になります

**特徴**:
- ノードを事前に `slurm.conf` で定義する必要がない
- ノード追加時は計算ノード側で `slurmd -Z --conf-server master:6817` により起動して登録
- ノード削除時は `scontrol delete NodeName=...` で削除
- Feature属性によりパーティションへの割り当てが決定

## CoreDNS

クラスタ内部の名前解決を提供する軽量DNSサーバーです。

**役割**:
- 動的に追加・削除される計算ノードのホスト名解決
- パーティション間の通信サポート
- `/opt/ohpc/pub/etc/hosts.ohpc` ファイルを5秒間隔で自動リロード

**設定**:

```bash
DNS_DOMAIN=ohpc.internal        # クラスタ内部ドメイン名
DNS_FORWARDERS="8.8.8.8,8.8.4.4"  # 外部DNS転送先（カンマ区切り）
```

**動作**:
1. マスターノードでCoreDNSが起動（マスターノードのIPアドレス:53にバインド）
   - systemd-resolvedとの競合を避けるため、特定IPアドレスにバインド
   - バインドIPアドレスは環境変数`PRIVATE_IP`から自動取得
2. 計算ノードはマスターノードをDNSサーバーとして設定
3. CoreDNSは `/opt/ohpc/pub/etc/hosts.ohpc` を参照してホスト名を解決
4. クラスタ外のホスト名は `DNS_FORWARDERS` に転送

**ホスト管理**:
- 初期ホストエントリは起動時に自動生成
- Feature（NodeSet）の追加・削除時にAnsibleが `/opt/ohpc/pub/etc/hosts.ohpc` を更新
- 更新は5秒以内に全ノードに反映

## GPU対応

GPUを使用する場合、以下の2段階の設定が必要です：

### 1. slurm.conf でのGPU宣言（Ansible管理）

AnsibleがFeature/Partition設定に基づき、以下を `slurm.conf` に追加します：

```bash
# GPU使用パーティションが存在する場合
GresTypes=gpu

# 各パーティションのNodeSet定義
NodeSet=ns-gpu-small Feature=aws-gpu-t4
NodeSet=ns-gpu-large Feature=aws-gpu-a100
PartitionName=gpu-small Nodes=ns-gpu-small
PartitionName=gpu-large Nodes=ns-gpu-large
```

各計算ノードのGPUリソースは、slurmd起動時に `-Z --conf "Gres=gpu:N"` オプションで宣言されます（`GPUS` 環境変数から設定）。

### 2. gres.conf（マスターノードに同梱）

マスターノードのイメージに `AutoDetect=nvidia` を設定した `gres.conf` が含まれています。
この設定はconfigless modeにより全計算ノードに自動配布されます。

GPU対応の計算ノードでは、NVIDIA GPUが自動検出されます（Slurm 24.11で追加された方式で、外部ライブラリ不要）。
非GPUノードではGPUが検出されないため、自動検出はスキップされます（エラーにはなりません）。

**要件**:
1. GPU対応イメージを使用：`compute-gpu-3.4-multi`
2. GPUS環境変数でGPU数を指定：`GPUS=1` または `GPUS=4`（slurmdのGRES宣言に使用）

## 参考資料

- [OpenHPC Documentation](https://openhpc.community/)
- [Slurm Documentation](https://slurm.schedmd.com/)
- [Slurm Configless Mode](https://slurm.schedmd.com/configless_slurm.html)
- [Slurm Dynamic Nodes](https://slurm.schedmd.com/dynamic_nodes.html)
