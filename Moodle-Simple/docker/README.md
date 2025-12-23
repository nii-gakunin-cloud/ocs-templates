# コンテナイメージのビルド

## ビルド方法

```console
 docker buildx bake
```

## イメージのタグ

### Moodleコンテナイメージ

|タグ|説明|
|:--|:--|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:5.1|Moodle 5.1|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:5.0|Moodle 5.0|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:4.5|Moodle 4.5 (LTS)|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:4.4|Moodle 4.4|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:4.1|Moodle 4.1 (LTS)|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:base|ベースコンテナイメージ|

### リバースプロキシコンテナイメージ

|タグ|説明|対応Moodleバージョン|
|:--|:--|:--|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:ssl-v5|TLS対応 (Moodle 5.1+)|5.1以降|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:ssl-v4|TLS対応 (Moodle 5.0以前)|4.1〜5.0|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:shibboleth-v5|Shibboleth対応 (Moodle 5.1+)|5.1以降|
|harbor.vcloud.nii.ac.jp/vcp/moodle-simple:shibboleth-v4|Shibboleth対応 (Moodle 5.0以前)|4.1〜5.0|
