<?php
// 標準以外のプラグインのディレクトリを $CFG->dirroot からの相対パスで出力する。
// サブプラグインなど、他のプラグインのディレクトリに含まれるものは出力しない。
// まだインストールしていないプラグインも対象とするため、キャッシュを使わずにディスクから取得する。
define('CLI_SCRIPT', true);
define('IGNORE_COMPONENT_CACHE', true);
require('/var/www/moodle/config.php');

$dirs = [];
foreach (core_plugin_manager::instance()->get_plugins() as $plugins) {
    foreach ($plugins as $plugin) {
        if ($plugin->is_standard() || empty($plugin->rootdir)) {
            continue;
        }
        if (strpos($plugin->rootdir, $CFG->dirroot . '/') !== 0) {
            continue;
        }
        $dirs[] = substr($plugin->rootdir, strlen($CFG->dirroot) + 1);
    }
}
sort($dirs);

$result = [];
foreach ($dirs as $dir) {
    $last = end($result);
    if ($last !== false && strpos($dir . '/', $last . '/') === 0) {
        continue;
    }
    $result[] = $dir;
}
foreach ($result as $dir) {
    echo $dir, "\n";
}
