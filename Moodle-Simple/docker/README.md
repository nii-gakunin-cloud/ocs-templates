# コンテナイメージのビルド

## ビルド方法

```console
 docker buildx bake
```

## イメージのタグ

### Moodleコンテナイメージ

|タグ|説明|
|:--|:--|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:5.3|Moodle 5.3 (LTS)|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:5.2|Moodle 5.2|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:5.1|Moodle 5.1|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:4.5|Moodle 4.5 (LTS)|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:base|ベースコンテナイメージ|

### リバースプロキシコンテナイメージ

|タグ|説明|対応Moodleバージョン|
|:--|:--|:--|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:ssl-v5|TLS対応 (Moodle 5.1+)|5.1以降|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:ssl-v4|TLS対応 (Moodle 4.5)|4.5|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:shibboleth-v5|Shibboleth対応 (Moodle 5.1+)|5.1以降|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:shibboleth-v4|Shibboleth対応 (Moodle 4.5)|4.5|
