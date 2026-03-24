# OpenHPC-v3 group_vars パラメータリファレンス

本ドキュメントは OpenHPC-v3 テンプレートの group_vars に記録される全パラメータについて説明します。

## ファイル構成

```
group_vars/
├── all.yml          # 全UnitGroup共通の変数（現在は未使用）
└── {ugroup_name}.yml  # UnitGroup固有の変数（全パラメータをここに記録）
```

---

## 1. 基盤パラメータ

| パラメータ | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|----|
| `ugroup_name` | str | Yes | UnitGroup名（英数字のみ） | `MyHPC` |
| `ssh_public_key_path` | str | Yes | SSH公開鍵のファイルパス | `~/.ssh/id_rsa.pub` |
| `ssh_private_key_path` | str | Yes | SSH秘密鍵のファイルパス | `~/.ssh/id_rsa` |
| `vault_path_munge_key` | str | Yes | Vault上のmunge.keyパス | `cubbyhole/OpenHPC/MyHPC/munge.key` |
| `cluster_name` | str | No | Slurmクラスタ名（デフォルト: `ugroup_name` と同一値） | `MyCluster` |
| `verify_ssl_certificate` | bool | No | VCPのSSL証明書検証（デフォルト: `true`） | `false` |

---

## 2. マスターノード構成

| パラメータ | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|----|
| `master_provider` | str | Yes | クラウドプロバイダ | `aws`, `azure`, `oracle`, `onpremises` |
| `master_flavor` | str | Yes | VCPフレーバー | `small`, `medium`, `large` |
| `master_instance_type` | str | No | インスタンスタイプ（flavor上書き） | `m7i.xlarge` |
| `master_root_size` | int | Yes | ルートボリュームサイズ（GB、20以上） | `60` |
| `master_ipaddress` | str | Yes | マスターノードのIPアドレス | `172.30.2.100` |
| `master_hostname` | str | Yes | マスターノードのホスト名 | `master` |
| `mdx_master_pack_num` | int | No | mdxのパック数（mdx環境のみ、3以上） | `3` |

---

## 3. slurm_features（Feature定義）

`slurm_features` は計算ノードグループ（Feature）を定義する辞書です。キーはFeature名、値はそのFeatureの構成パラメータです。

```yaml
slurm_features:
  {feature_name}:
    vc_unit: ...
    provider: ...
    ...
```

### Feature名の命名規則

- 英小文字・数字・ハイフンのみ使用可能
- 2〜64文字
- `master` は使用不可

### フィールド一覧

| フィールド | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|----|
| `vc_unit` | str | Yes | VCユニット名（現在はFeature名と同一値） | `gpu-a100` |
| `provider` | str | Yes | クラウドプロバイダ | `aws`, `azure`, `oracle`, `onpremises` |
| `flavor` | str | Yes | VCPフレーバー | `medium`, `gpu`, `default` |
| `use_gpu` | bool | Yes | GPU使用の有無 | `true`, `false` |
| `gpus` | int | Yes | ノードあたりのGPU数（GPU未使用時は `0`） | `0`, `1`, `4` |
| `nodes` | int | Yes | 現在の稼働ノード数 | `4` |
| `ip_addresses` | list[str] | Yes | 割り当て可能な全IPアドレスのリスト | `["172.30.2.121", ...]` |
| `hostname_template` | str | Yes | ホスト名テンプレート（Pythonフォーマット文字列） | `c{}`, `gpu{:02}` |
| `instance_type` | str | No | インスタンスタイプ（flavor上書き） | `g5.xlarge` |
| `root_size` | int | No | ルートボリュームサイズ（GB） | `60` |
| `nfs_entries` | str | No | 追加NFSマウント設定（Base64エンコード済み） | ― |
| `mdx_pack_num` | int | No | mdxのパック数（mdx環境のみ） | `3` |
| `docker` | bool | No | Docker Engineインストール済みフラグ | `true` |

### フィールド詳細

**`vc_unit`**: VCP SDKでVCユニットを操作する際の識別名。現在の実装ではFeature名と同一値が設定されます。将来的にFeature名と異なる値を設定できるよう拡張予定です。

**`nodes` と `ip_addresses` の関係**: `nodes` は現在稼働中のノード数、`ip_addresses` は割り当て可能なIPアドレスの全リストです。常に `nodes <= len(ip_addresses)` が成り立ちます。`ip_addresses` の長さがスケールアップ可能な最大ノード数となります。

**`hostname_template`**: Pythonの `str.format()` で展開されるテンプレートです。引数はノードのインデックス（1始まり）です。
- `c{}` → c1, c2, c3, ...
- `c{:02}` → c01, c02, c03, ...
- `gpu{:02}` → gpu01, gpu02, ...

異なるFeature間でホスト名が衝突しないよう、バリデーションが行われます。

**`nfs_entries`**: 計算ノードに追加するNFSマウントのfstabエントリをBase64エンコードした文字列です。エンコード前の形式は標準的なfstab形式（`server:/path /mount/point nfs options 0 0`）です。

**`docker`**: 071-DockerEngineのインストール Notebook の実行時に `true` が設定されます。スケジュール設定（811/812）のPlaybook実行時にこのフラグが参照され、Docker Composeベースのスケジュール実行環境を構成するかどうかが決定されます。

### 設定例

```yaml
slurm_features:
  cpu-aws:
    vc_unit: cpu-aws
    provider: aws
    flavor: medium
    use_gpu: false
    gpus: 0
    nodes: 4
    ip_addresses:
      - "172.30.2.131"
      - "172.30.2.132"
      - "172.30.2.133"
      - "172.30.2.134"
      - "172.30.2.135"
      - "172.30.2.136"
    hostname_template: "c{:02}"
  gpu-a100:
    vc_unit: gpu-a100
    provider: aws
    flavor: gpu
    instance_type: g5.xlarge
    use_gpu: true
    gpus: 1
    nodes: 2
    ip_addresses:
      - "172.30.2.141"
      - "172.30.2.142"
      - "172.30.2.143"
      - "172.30.2.144"
    hostname_template: "gpu{:02}"
    root_size: 60
    docker: true
```

---

## 4. slurm_partitions（Partition定義）

`slurm_partitions` はSlurmのPartitionを定義する辞書です。キーはPartition名、値はそのPartitionの構成パラメータです。

```yaml
slurm_partitions:
  {partition_name}:
    nodesets: [...]
    default: ...
```

### Partition名の命名規則

- 英数字・ハイフン・アンダースコアが使用可能
- 2〜64文字

### フィールド一覧

| フィールド | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|----|
| `nodesets` | list[str] | Yes | 所属するNodeSet名のリスト | `["ns-cpu-aws"]` |
| `default` | bool | Yes | デフォルトPartitionか否か（全体で1つのみ `true`） | `true` |
| `allow_groups` | list[str] | No | アクセスを許可するUNIXグループ（省略時は全ユーザ許可） | `["gpu-users"]` |

### NodeSet名の導出規則

NodeSet名はFeature名から自動生成されます。group_varsに直接記録されるものではなく、`slurm_partitions` の `nodesets` リスト内と `slurm.conf` テンプレートで使用されます。

```
NodeSet名 = "ns-" + Feature名
```

例: Feature名 `gpu-a100` → NodeSet名 `ns-gpu-a100`

### PartitionとFeatureの関係

- 1つのPartitionに複数のFeature（NodeSet）を割り当てることができます（異種混在Partition）
- 1つのFeatureは複数のPartitionに所属できます
- デフォルトPartitionは全体で1つだけです

### 設定例

```yaml
slurm_partitions:
  compute:
    nodesets:
      - ns-cpu-aws
    default: true
  gpu:
    nodesets:
      - ns-gpu-a100
    default: false
    allow_groups:
      - gpu-users
      - researchers
```

---

## 5. slurm_custom_conf_content（カスタムSlurm設定）

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `slurm_custom_conf_content` | str | No | `slurm.conf` に追加するカスタム設定（複数行可） |

Ansibleが生成する `slurm.conf` の末尾に、この内容がそのまま追記されます。

### 使用できない設定項目

以下のパラメータはAnsibleが自動管理するため、`slurm_custom_conf_content` に含めることはできません（バリデーションエラーとなります）。

- `ClusterName`, `SlurmctldHost`
- `NodeSet`, `PartitionName`
- `MaxNodeCount`, `GresTypes`

### 設定例

```yaml
slurm_custom_conf_content: |
  DefMemPerCPU=1024
  MaxJobCount=10000
```

---

## 6. DNS設定

| パラメータ | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|----|
| `dns_forwarders` | list[str] | Yes | 外部DNS転送先 | `["8.8.8.8", "8.8.4.4"]` |
| `dns_domain` | str | No | クラスタ内部ドメイン名（デフォルト: `ohpc.internal`） | `ohpc.internal` |

---

## 7. NFS/ストレージ

マスターノードのNFSボリュームに関する設定です。

| パラメータ | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|----|
| `nfs_disk_size` | int | No | NFSボリュームサイズ（GB、16以上） | `64` |
| `nfs_device` | str | 条件付き | デバイスパス（`nfs_disk_size` 指定時は必須） | `/dev/nvme1n1` |

計算ノード固有の追加NFSマウントは `slurm_features` の `nfs_entries` フィールドで管理します。

---

## 8. スケジュール設定

計算ノード数の時間帯別自動変更に関する設定です。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `vcnode_schedule_target_feature` | str | 条件付き | スケジュール対象のFeature名（スケジュール使用時は必須） |
| `vcnode_schedule` | dict | No | スケジュール定義 |

### vcnode_schedule の構造

```yaml
vcnode_schedule:
  default:
    node_count: 2         # 通常時のノード数
    max_node_count: 10    # 最大ノード数（= ip_addressesの長さ）
    down_type: power_down # ノード停止方法（power_down または deleted）
    drain_time: 0         # DRAIN状態の維持時間（秒）
  schedule:
    - node_count: 5       # 変更後のノード数
      period:
        begin: {hour: 8, minute: 0}
        end: {hour: 18, minute: 0}
```

### period の指定方法

| 粒度 | フィールド | 例 |
|------|-----------|-----|
| 日毎 | `hour`, `minute` | `{hour: 8, minute: 0}` |
| 週毎 | `day_of_week`, `hour`, `minute` | `{day_of_week: 1, hour: 9, minute: 0}`（1=月曜） |
| 月毎 | `day`, `hour`, `minute` | `{day: 1, hour: 0, minute: 0}` |
| 年毎 | `month`, `day`, `hour`, `minute` | `{month: 4, day: 1, hour: 0, minute: 0}` |
| 特定日時 | `year`, `month`, `day`, `hour`, `minute` | `{year: 2026, month: 3, day: 15, hour: 9, minute: 0}` |

---

## 9. mdx固有パラメータ

mdx（オンプレミス）環境でのみ使用するパラメータです。

| パラメータ | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|----|
| `mdx_ssh_user_name` | str | No | mdx SSHユーザ名（デフォルト: `mdxuser`） | `mdxuser` |
| `mdx_project_name` | str | No | mdxプロジェクト名 | ― |
| `mdx_segment_id` | str | No | mdxネットワークセグメントのUUID | ― |

---

## Ansibleテンプレートでの利用

group_vars のパラメータは、Ansibleの `openhpc-slurm` ロールにより以下のファイルを生成する際に参照されます。

### slurm.conf（Slurmクラスタ設定）

| 生成される設定項目 | 参照元 |
|------------------|--------|
| `ClusterName` | `cluster_name`（未定義時は `ugroup_name`） |
| `SlurmctldHost` | `master_hostname` |
| `GresTypes=gpu` | `slurm_features` のいずれかで `use_gpu: true` の場合に出力 |
| `MaxNodeCount` | 全Featureの `ip_addresses` の長さの合計 |
| `NodeSet=ns-{name} Feature={name}` | `slurm_features` の各エントリから生成 |
| `PartitionName=...` | `slurm_partitions` の各エントリから生成 |
| カスタム設定 | `slurm_custom_conf_content` |

### hosts.ohpc（CoreDNS用ホスト定義）

| 生成される内容 | 参照元 |
|---------------|--------|
| マスターノードのエントリ | `master_ipaddress`, `master_hostname`, `dns_domain` |
| 計算ノードのエントリ | `slurm_features` の各Featureの `ip_addresses` と `hostname_template` |

ホスト名は `hostname_template.format(index)` で生成されます（indexは1始まり）。各エントリには短縮名とFQDN（`{hostname}.{dns_domain}`）の両方が記録されます。

---

## ヘルパー関数

パラメータの読み書きは `scripts/group.py` の以下の関数で行います。

| 関数 | 用途 |
|------|------|
| `load_group_vars(ugroup_name)` | 全パラメータを読み込み（all.yml とUnitGroup固有を統合） |
| `update_group_vars(ugroup_name, **kwargs)` | 任意のパラメータを追加・更新 |
| `update_slurm_features(ugroup_name, feature_name, config)` | Feature定義を追加・更新 |
| `update_slurm_partitions(ugroup_name, partition_name, config)` | Partition定義を追加・更新 |
| `delete_slurm_feature(ugroup_name, feature_name)` | Feature定義を削除 |
| `add_feature_to_partition(ugroup_name, partition_name, feature_name)` | PartitionにFeatureを追加 |
| `remove_feature_from_partition(ugroup_name, partition_name, feature_name)` | PartitionからFeatureを除外 |
| `set_default_partition(ugroup_name, partition_name)` | デフォルトPartitionを変更 |
| `update_partition_allow_groups(ugroup_name, partition_name, groups)` | Partitionのアクセス制御を設定 |
| `update_slurm_custom_conf(ugroup_name, content)` | カスタムSlurm設定を更新 |

---

## 完全な設定例

```yaml
# 基盤
ugroup_name: MyHPC
ssh_public_key_path: /home/user/.ssh/id_rsa.pub
ssh_private_key_path: /home/user/.ssh/id_rsa
vault_path_munge_key: cubbyhole/OpenHPC/MyHPC/munge.key

# マスターノード
master_provider: aws
master_flavor: medium
master_root_size: 60
master_ipaddress: 172.30.2.100
master_hostname: master

# DNS
dns_forwarders:
  - "8.8.8.8"
  - "8.8.4.4"
dns_domain: ohpc.internal

# NFS
nfs_disk_size: 64
nfs_device: /dev/nvme1n1

# Feature定義
slurm_features:
  cpu-aws:
    vc_unit: cpu-aws
    provider: aws
    flavor: medium
    use_gpu: false
    gpus: 0
    nodes: 4
    ip_addresses:
      - "172.30.2.131"
      - "172.30.2.132"
      - "172.30.2.133"
      - "172.30.2.134"
      - "172.30.2.135"
      - "172.30.2.136"
    hostname_template: "c{:02}"
  gpu-a100:
    vc_unit: gpu-a100
    provider: aws
    flavor: gpu
    instance_type: g5.xlarge
    use_gpu: true
    gpus: 1
    nodes: 2
    ip_addresses:
      - "172.30.2.141"
      - "172.30.2.142"
      - "172.30.2.143"
      - "172.30.2.144"
    hostname_template: "gpu{:02}"
    root_size: 60
    docker: true

# Partition定義
slurm_partitions:
  compute:
    nodesets:
      - ns-cpu-aws
    default: true
  gpu:
    nodesets:
      - ns-gpu-a100
    default: false
    allow_groups:
      - gpu-users

# カスタムSlurm設定（任意）
slurm_custom_conf_content: |
  DefMemPerCPU=1024

# スケジュール設定（任意）
vcnode_schedule_target_feature: cpu-aws
vcnode_schedule:
  default:
    node_count: 4
    max_node_count: 6
    down_type: power_down
    drain_time: 0
  schedule:
    - node_count: 2
      period:
        begin: {hour: 22, minute: 0}
        end: {hour: 7, minute: 0}
```
