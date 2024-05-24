import os
import re
import shutil
import sys
from datetime import datetime
from itertools import chain, zip_longest
from pathlib import Path
from subprocess import CalledProcessError, run
from tempfile import TemporaryDirectory

from jinja2 import Template
from lxml import etree
from nbformat import NO_CONVERT, read

TITLE_FONT_SIZE = 11
ITEM_FONT_SIZE = 9
HEAD_MARGIN = 3
TEXT_MARGIN = 2

SVG_TEXT = "{http://www.w3.org/2000/svg}text"
SVG_RECT = "{http://www.w3.org/2000/svg}rect"

NB_GROUP = {
    "group-cwh": "[01234789]*-*.ipynb",
    "group-idp": "5*-*.ipynb",
}


def parse_headers(nb_path):
    nb = read(str(nb_path), as_version=NO_CONVERT)

    # Notebookのセルからmarkdownの部分を取り出し、行ごとのリストにする
    lines = [
        line.strip()
        for line in chain.from_iterable(
            cell["source"].split("\n")
            for cell in nb.cells
            if cell["cell_type"] == "markdown"
        )
        if len(line.strip()) > 0 and not line.startswith("---")
    ]

    # h1, h2 の行とその次行の最初の１文を取り出す
    headers = [
        (" ".join(line0.split()[1:]), line1.split("。")[0] if line1 is not None else "")
        for (line0, line1) in zip_longest(lines, lines[1:])
        if line0.startswith("# ") or line0.startswith("## ")
    ]

    # 最初の見出しはtitle, 残りはheadersとして返す
    return {
        "title": {
            "text": _to_title_text(nb_path, headers[0][0]),
            "summary": headers[0][1],
        },
        "headers": [
            {
                "text": text,
                "summary": (summary if not re.match(r"(?:#|!\[)", summary) else ""),
            }
            for (text, summary) in headers[1:]
        ],
    }


def _to_title_text(nb_path, text):
    no = nb_path.name.split("-")[0]
    title = text if not text.startswith("About:") else text[6:]
    return f"{no}: {title}"


def create_text(rect, font_size, font_weight="normal", font_style="normal"):
    text_elem = etree.Element(SVG_TEXT)
    text_elem.attrib["fill"] = "rgb(0,0,0)"
    text_elem.attrib["font-family"] = "sans-serif"
    text_elem.attrib["font-size"] = str(font_size)
    text_elem.attrib["font-style"] = font_style
    text_elem.attrib["font-weight"] = font_weight
    text_elem.attrib["font-anchor"] = "middle"
    text_elem.attrib["x"] = str(rect[0][0] + TEXT_MARGIN)
    text_elem.attrib["width"] = str(rect[1][0] - TEXT_MARGIN * 2)
    return text_elem


def create_anchor(elems, link):
    a_elem = etree.Element("a")
    a_elem.attrib["{http://www.w3.org/1999/xlink}href"] = link
    for elem in elems:
        a_elem.append(elem)
    return a_elem


def split_title(title):
    if "：" in title:
        return [title[: title.index("：") + 1], title[title.index("：") + 1 :]]
    if len(title) >= 15:
        words = re.split(r"([(（]|-{2,})", title, 1)
        ret = words[0:1] + ["".join(x) for x in zip(words[1::2], words[2::2])]
        return [re.sub(r"^--", "- ", x) for x in ret]

    return [title]


def insert_title(parent_elem, childpos, rect, title, link):
    height_title = TEXT_MARGIN + (TITLE_FONT_SIZE + TEXT_MARGIN) * 2 + HEAD_MARGIN * 2
    lines = split_title(title)
    if len(lines) == 2:
        text_elem = create_text(rect, TITLE_FONT_SIZE, font_weight="bold")
        text_elem.text = lines[0]
        text_elem.attrib["y"] = str(
            rect[0][1] + HEAD_MARGIN + TEXT_MARGIN + TITLE_FONT_SIZE
        )
        text_elems = [text_elem]

        text_elem = create_text(rect, TITLE_FONT_SIZE, font_weight="bold")
        text_elem.text = lines[1]
        text_elem.attrib["y"] = str(
            rect[0][1] + height_title - TEXT_MARGIN - HEAD_MARGIN
        )
        text_elems.append(text_elem)
    else:
        text_elem = create_text(rect, TITLE_FONT_SIZE, font_weight="bold")
        text_elem.text = title
        text_elem.attrib["y"] = str(
            rect[0][1] + height_title // 2 + TITLE_FONT_SIZE // 2
        )
        text_elems = [text_elem]

    parent_elem.insert(childpos, create_anchor(text_elems, link))
    return len(lines)


def insert_headers(parent_elem, childpos, rect, headers, title_lines):
    offset_y = (
        TEXT_MARGIN
        + (TITLE_FONT_SIZE + TEXT_MARGIN) * (title_lines + 1)
        + HEAD_MARGIN * 2
        + TEXT_MARGIN
    )
    for i, header in enumerate(headers):
        text_elem = create_text(rect, ITEM_FONT_SIZE)
        text_elem.text = header["text"]
        text_elem.attrib["y"] = str(
            rect[0][1] + offset_y + (ITEM_FONT_SIZE + TEXT_MARGIN) * i + ITEM_FONT_SIZE
        )
        parent_elem.insert(childpos, text_elem)


def remove_texts(elem):
    old_text = elem
    while old_text is not None:
        if old_text.getnext() is not None and old_text.getnext().tag == SVG_TEXT:
            next_text = old_text.getnext()
        else:
            next_text = None
        old_text.getparent().remove(old_text)
        old_text = next_text


def _get_notebook_headers(nb_dir, nb_group=None):
    pattern = NB_GROUP.get(nb_group, "[0-9]*-*.ipynb")
    return dict((nb.name, parse_headers(nb)) for nb in nb_dir.glob(pattern))


def _embed_info_in_one_rect(elem, nb_headers, nb_dir, nb_name):
    headers = nb_headers[nb_name]
    nb_file = nb_dir / nb_name
    rect_elem = elem.getprevious()
    rect = (
        (int(rect_elem.attrib["x"]), int(rect_elem.attrib["y"])),
        (int(rect_elem.attrib["width"]), int(rect_elem.attrib["height"])),
    )
    childpos = elem.getparent().index(elem)
    parent_elem = elem.getparent()
    remove_texts(elem)
    title = headers["title"]["text"]
    if elem.text.find(":") >= 0:
        title = title + " - " + elem.text.split(":")[1]
    line_num = insert_title(parent_elem, childpos, rect, title, str(nb_file))
    insert_headers(parent_elem, childpos, rect, headers["headers"], line_num)


def _find_matching_notebook(notebooks, prefix):
    nb_prefix = prefix if prefix.find(":") < 0 else prefix.split(":")[0]
    for nb in notebooks:
        if nb.startswith(nb_prefix):
            return nb


def _is_target_rect(elem, notebooks):
    return (
        elem.getprevious() is not None
        and elem.getprevious().tag == SVG_RECT
        and len(elem.text) > 0
        and _find_matching_notebook(notebooks, elem.text) is not None
    )


def _embed_detail_information(output, skeleton, nb_dir):
    # Notebookのヘッダ取得
    nb_headers = _get_notebook_headers(nb_dir)

    # 雛形の読み込み
    tree = etree.parse(str(skeleton))

    # 雛形をNotebook情報で置き換え
    for elem in list(tree.findall(SVG_TEXT)):
        if _is_target_rect(elem, nb_headers.keys()):
            nb_name = _find_matching_notebook(nb_headers.keys(), elem.text)
            _embed_info_in_one_rect(elem, nb_headers, nb_dir, nb_name)

    # SVGの保存
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open(mode="wb") as f:
        f.write(etree.tostring(tree, method="xml", pretty_print=True))


def _generate_skeleton(output, diag, font):
    run(["blockdiag", "-f", font, "-Tsvg", "-o", output, diag], check=True)


def generate_svg_diag(
    output="images/notebooks.svg",
    diag="images/notebooks.diag",
    nb_dir="notebooks",
    font="/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
):
    with TemporaryDirectory() as workdir:
        skeleton = Path(workdir) / "skeleton.svg"
        _generate_skeleton(skeleton, Path(diag), Path(font))
        _embed_detail_information(Path(output), skeleton, Path(nb_dir))
        return output


def notebooks_toc(nb_dir="notebooks"):
    nb_headers = sorted(_get_notebook_headers(Path(nb_dir)).items(), key=lambda x: x[0])
    return "\n".join(
        chain.from_iterable(
            [
                [f'* [{headers["title"]["text"]}]({nb_dir}/{str(nb)})']
                + list(
                    chain.from_iterable(
                        [
                            [
                                f'    1. {header["text"]}',
                                (
                                    f'        - {header["summary"]}'
                                    if len(header["summary"]) > 0
                                    else ""
                                ),
                            ]
                            for header in headers["headers"]
                        ]
                    )
                )
                for nb, headers in nb_headers
            ]
        )
    )


def setup_blockdiag():
    if not check_blockdiag():
        install_blockdiag()
    return check_blockdiag()


def check_blockdiag():
    try:
        run("blockdiag -h", shell=True, check=True, capture_output=True)
        return True
    except CalledProcessError:
        return False


def install_blockdiag():
    run("pip install -q --force-reinstall --user blockdiag", shell=True)
    paths = os.environ["PATH"].split(":")
    local_bin = str(Path("~/.local/bin").expanduser())
    if local_bin not in paths:
        paths.append(local_bin)
        os.environ["PATH"] = ":".join(paths)
    if not check_blockdiag():
        install_blockdiag()


def setup_lxml():
    if not check_lxml():
        install_lxml()
    return check_lxml()


def check_lxml():
    try:
        import lxml

        return True
    except ModuleNotFoundError:
        return False


def install_lxml():
    run("pip install -q --user lxml", shell=True)
    setup_python_path()


def setup_python_path():
    ver = sys.version_info
    lib_path = f"~/.local/lib/python{ver.major}.{ver.minor}/site-packages"
    lib_path = str(Path(lib_path).expanduser())
    if lib_path not in sys.path:
        sys.path.append(lib_path)


def setup_diag():
    setup_blockdiag()
    setup_lxml()


def setup_nb_workdir(work_dir):
    work = Path(work_dir)
    if not work.exists():
        work.mkdir(parents=True, exist_ok=True)
    for sub_dir in ["notebooks/images", "scripts", "playbooks", "template", "docker"]:
        dst_dir = (work / Path(sub_dir).name).resolve()
        src_dir = Path(sub_dir).resolve()
        if src_dir.exists() and not dst_dir.exists():
            dst_dir.symlink_to(src_dir, target_is_directory=True)
    dst_gvars = work / "group_vars"
    src_gvars = Path("group_vars")
    if src_gvars.exists() and not dst_gvars.exists():
        shutil.copytree(src_gvars, dst_gvars)


def generate_html_work_nbs(work_dir, nb_dir="notebooks", nb_group=None):
    nb_path = Path(nb_dir)
    nb_items = dict(
        (str(nb_path / nb), header["title"]["text"])
        for nb, header in _get_notebook_headers(nb_path, nb_group).items()
    )
    return Template(
        """
<script type="text/Javascript">
    function generate_win_name() {
        return Array.from(Array(15), (v, k) => k).map(
            x => Math.floor(Math.random() * 16).toString(16)
        ).join("");
    }
    function copy_otehon(work_dir, group) {
        let sel = document.getElementById('selector-' + group);
        let kernel = IPython.notebook.kernel;
        let win_name = generate_win_name();
        let callbacks = {'iopub': {'output': function(msg) {
                let lines = msg.content.text.trim().split("\\n");
                window.open(lines.length > 1 ? lines[1] : lines[0], win_name);
            }}};
        window.open('', win_name);
        kernel.execute('copy_ref_notebook("'
            + sel.options[sel.selectedIndex].value
            + '", "' + work_dir + '", trusted=True)', callbacks);
    }
</script>
<select id="selector-{{group}}">
{% for key, value in notebooks.items()|sort %}
<option value="{{key}}">{{value}}</option>
{% endfor %}
</select>
<button onclick="copy_otehon('{{work_dir}}', '{{group}}')">作業開始</button>
"""
    ).render(work_dir=work_dir, notebooks=nb_items, group=nb_group)


def copy_ref_notebook(src_nb, dest_dir, trusted=False):
    dest_nb = _get_dest_nb_path(src_nb, dest_dir)
    shutil.copyfile(src_nb, dest_nb)
    if trusted:
        run(["jupyter", "trust", dest_nb], check=False)
    print(dest_nb)


def _get_dest_nb_path(src_nb_path, dest_dir):
    prefix = datetime.now().strftime("%Y%m%d")
    src_path = Path(src_nb_path)
    dest_path = Path(dest_dir)
    index = len(list(dest_path.glob(f"{prefix}*"))) + 1
    return str(dest_path / f"{prefix}_{index:0>2}_{src_path.name}")
