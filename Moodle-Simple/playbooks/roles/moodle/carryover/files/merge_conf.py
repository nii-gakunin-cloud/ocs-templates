"""利用者が変更した設定ファイルを、新しいコンテナイメージの設定ファイルに引き継ぐ。

更新前のイメージの設定ファイル（base）から退避した設定ファイル（mine）への変更を、
新しいイメージの設定ファイル（new）に diff3 で当てる。

usage: merge_conf.py BASE MINE NEW REPORT
"""
import filecmp
import os
import shutil
import subprocess
import sys

# ca-trust はイメージに対応するものがないため、別のタスクでそのままコピーする
EXCLUDE = {"ca-trust"}
# ansible の backup=yes で作成された控え（*.{pid}.{日時}~）は引き継がない
BACKUP_SUFFIX = "~"

LABELS = {
    "copied": "引き継ぎ（変更したファイルをそのまま配置）",
    "merged": "引き継ぎ（変更を新しいファイルにマージ）",
    "added": "引き継ぎ（追加したファイルを配置）",
    "conflict": "要確認（変更を自動で引き継げない）",
    "removed": "要確認（新しいイメージにはないファイル）",
}


def entries(root):
    result = set()
    for dirpath, dirnames, filenames in os.walk(root):
        links = [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]
        for name in filenames + links:
            result.add(os.path.relpath(os.path.join(dirpath, name), root))
    return result


def same(a, b):
    if os.path.islink(a) or os.path.islink(b):
        return os.path.islink(a) and os.path.islink(b) and os.readlink(a) == os.readlink(b)
    return filecmp.cmp(a, b, shallow=False)


def copy(src, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.lexists(dest):
        os.remove(dest)
    if os.path.islink(src):
        os.symlink(os.readlink(src), dest)
    else:
        shutil.copy2(src, dest)
        st = os.stat(src)
        os.chown(dest, st.st_uid, st.st_gid)


def diff(a, b):
    result = subprocess.run(["diff", "-u", a, b], capture_output=True, text=True)
    return result.stdout


def merge(base, mine, new):
    has_base = os.path.isdir(base) and len(os.listdir(base)) > 0
    results = []
    for rel in sorted(entries(mine)):
        if rel.split(os.sep)[0] in EXCLUDE or rel.endswith(BACKUP_SUFFIX):
            continue
        m, b, n = (os.path.join(d, rel) for d in (mine, base, new))
        in_base = has_base and os.path.lexists(b)
        in_new = os.path.lexists(n)
        if in_new and same(m, n):
            continue
        if in_base and same(m, b):
            # 利用者が変更していない
            continue
        if not in_new:
            if in_base:
                results.append(("removed", rel, diff(b, m)))
            else:
                copy(m, n)
                results.append(("added", rel, ""))
            continue
        if in_base and same(n, b):
            copy(m, n)
            results.append(("copied", rel, ""))
            continue
        if not in_base or any(os.path.islink(x) for x in (m, b, n)):
            results.append(("conflict", rel, diff(n, m)))
            continue
        merged = subprocess.run(["diff3", "-m", m, b, n], capture_output=True)
        if merged.returncode == 0:
            with open(n, "wb") as f:
                f.write(merged.stdout)
            results.append(("merged", rel, ""))
        else:
            results.append(("conflict", rel, diff(b, m)))
    return has_base, results


def main():
    base, mine, new, report = sys.argv[1:5]
    has_base, results = merge(base, mine, new)
    lines = []
    if not has_base:
        lines.append("更新前のイメージの設定ファイルを取得できなかったため、変更を自動で引き継いでいません。")
    if not results:
        lines.append("引き継ぐ変更はありません。")
    for kind, rel, _ in results:
        lines.append(f"{LABELS[kind]}: {rel}")
    for kind, rel, text in results:
        if text:
            lines.append("")
            lines.append(f"===== {rel}")
            lines.append(text.rstrip("\n"))
    output = "\n".join(lines) + "\n"
    with open(report, "w") as f:
        f.write(output)
    print(output, end="")


if __name__ == "__main__":
    main()
