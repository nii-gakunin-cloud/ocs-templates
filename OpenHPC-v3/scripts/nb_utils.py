import re
from datetime import datetime
from itertools import chain, zip_longest
from os import PathLike
from pathlib import Path
from shutil import copyfile, copytree
from subprocess import run
from tempfile import TemporaryDirectory
from typing import Dict, Iterable, List, Optional, Tuple, TypedDict

from jinja2 import Template
from lxml import etree
from nbformat import NO_CONVERT, read

TITLE_FONT_SIZE = 11
ITEM_FONT_SIZE = 9
HEAD_MARGIN = 3
TEXT_MARGIN = 2

SVG_TEXT = "{http://www.w3.org/2000/svg}text"
SVG_RECT = "{http://www.w3.org/2000/svg}rect"

DEFAULT_NB_PATTERN = "[0-9]*-*.ipynb"

Element = etree._Element  # pylint: disable=protected-access
Rect = Tuple[Tuple[int, int], Tuple[int, int]]
StrPath = str | PathLike[str]
HeaderDict = TypedDict("HeaderDict", {"text": str, "summary": str})
HeadersDict = TypedDict(
    "HeadersDict", {"title": HeaderDict, "headers": List[HeaderDict]}
)


def _parse_headers(nb_path: Path) -> HeadersDict:
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


def _to_title_text(nb_path: Path, text: str) -> str:
    no = nb_path.name.split("-")[0]
    title = text if not text.startswith("About:") else text[6:]
    return f"{no}: {title}"


def _create_text(
    rect: Rect, font_size: int, font_weight: str = "normal", font_style: str = "normal"
) -> Element:
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


def _create_anchor(elems: List[Element], link: str) -> Element:
    a_elem = etree.Element("a")
    a_elem.attrib["{http://www.w3.org/1999/xlink}href"] = link
    for elem in elems:
        a_elem.append(elem)
    return a_elem


def _split_title(title: str) -> List[str]:
    if "：" in title:
        return [title[: title.index("：") + 1], title[title.index("：") + 1 :]]
    if len(title) >= 15:
        words = re.split(r"([(（]|-{2,})", title, 1)
        ret = words[0:1] + ["".join(x) for x in zip(words[1::2], words[2::2])]
        return [re.sub(r"^--", "- ", x) for x in ret]

    return [title]


def _insert_title(
    parent_elem: Element, childpos: int, rect: Rect, title: str, link: str
) -> int:
    height_title = TEXT_MARGIN + (TITLE_FONT_SIZE + TEXT_MARGIN) * 2 + HEAD_MARGIN * 2
    lines = _split_title(title)
    if len(lines) == 2:
        text_elem = _create_text(rect, TITLE_FONT_SIZE, font_weight="bold")
        text_elem.text = lines[0]
        text_elem.attrib["y"] = str(
            rect[0][1] + HEAD_MARGIN + TEXT_MARGIN + TITLE_FONT_SIZE
        )
        text_elems = [text_elem]

        text_elem = _create_text(rect, TITLE_FONT_SIZE, font_weight="bold")
        text_elem.text = lines[1]
        text_elem.attrib["y"] = str(
            rect[0][1] + height_title - TEXT_MARGIN - HEAD_MARGIN
        )
        text_elems.append(text_elem)
    else:
        text_elem = _create_text(rect, TITLE_FONT_SIZE, font_weight="bold")
        text_elem.text = title
        text_elem.attrib["y"] = str(
            rect[0][1] + height_title // 2 + TITLE_FONT_SIZE // 2
        )
        text_elems = [text_elem]

    parent_elem.insert(childpos, _create_anchor(text_elems, link))
    return len(lines)


def _insert_headers(
    parent_elem: Element,
    childpos: int,
    rect: Rect,
    headers: List[HeaderDict],
    title_lines: int,
) -> None:
    offset_y = (
        TEXT_MARGIN
        + (TITLE_FONT_SIZE + TEXT_MARGIN) * (title_lines + 1)
        + HEAD_MARGIN * 2
        + TEXT_MARGIN
    )
    for i, header in enumerate(headers):
        text_elem = _create_text(rect, ITEM_FONT_SIZE)
        text_elem.text = header["text"]
        text_elem.attrib["y"] = str(
            rect[0][1] + offset_y + (ITEM_FONT_SIZE + TEXT_MARGIN) * i + ITEM_FONT_SIZE
        )
        parent_elem.insert(childpos, text_elem)


def _remove_texts(elem: Element) -> None:
    old_text: Optional[Element] = elem
    while old_text is not None:
        if (next_el := old_text.getnext()) is not None and next_el.tag == SVG_TEXT:
            next_text = next_el
        else:
            next_text = None
        parent = old_text.getparent()
        assert parent is not None
        parent.remove(old_text)
        old_text = next_text


def _get_notebook_headers(
    nb_dir: Path, nb_pattern: str = DEFAULT_NB_PATTERN
) -> Dict[str, HeadersDict]:
    return dict((nb.name, _parse_headers(nb)) for nb in nb_dir.glob(nb_pattern))


def _embed_info_in_one_rect(
    elem: Element, nb_headers: Dict[str, HeadersDict], nb_dir: Path, nb_name: str
) -> None:
    headers = nb_headers[nb_name]
    nb_file = nb_dir / nb_name
    if (rect_elem := elem.getprevious()) is None:
        return
    rect = (
        (int(rect_elem.attrib["x"]), int(rect_elem.attrib["y"])),
        (int(rect_elem.attrib["width"]), int(rect_elem.attrib["height"])),
    )
    parent_elem = elem.getparent()
    assert parent_elem is not None
    childpos = parent_elem.index(elem)
    _remove_texts(elem)
    title = headers["title"]["text"]
    if (text := elem.text) is not None and text.find(":") >= 0:
        title = title + " - " + text.split(":")[1]
    line_num = _insert_title(parent_elem, childpos, rect, title, str(nb_file))
    _insert_headers(parent_elem, childpos, rect, headers["headers"], line_num)


def _find_matching_notebook(notebooks: Iterable[str], prefix: str) -> Optional[str]:
    nb_prefix = prefix if prefix.find(":") < 0 else prefix.split(":")[0]
    for nb in notebooks:
        if nb.startswith(nb_prefix):
            return nb
    return None


def _is_target_rect(elem: Element, notebooks: Iterable[str]) -> bool:
    return (
        (previous := elem.getprevious()) is not None
        and previous.tag == SVG_RECT
        and elem.text is not None
        and len(elem.text) > 0
        and _find_matching_notebook(notebooks, elem.text) is not None
    )


def _embed_detail_information(output: Path, skeleton: StrPath, nb_dir: Path) -> None:
    # Notebookのヘッダ取得
    nb_headers = _get_notebook_headers(nb_dir)

    # 雛形の読み込み
    tree = etree.parse(str(skeleton))

    # 雛形をNotebook情報で置き換え
    for elem in list(tree.findall(SVG_TEXT)):
        if _is_target_rect(elem, nb_headers.keys()) and elem.text is not None:
            if (
                nb_name := _find_matching_notebook(nb_headers.keys(), elem.text)
            ) is not None:
                _embed_info_in_one_rect(elem, nb_headers, nb_dir, nb_name)

    # SVGの保存
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open(mode="wb") as f:
        f.write(etree.tostring(tree, method="xml", pretty_print=True))


def _generate_skeleton(output: StrPath, diag: StrPath, font: StrPath) -> None:
    run(["blockdiag", "-f", font, "-Tsvg", "-o", output, diag], check=True)


def generate_svg_diag(
    output: StrPath = "images/notebooks.svg",
    diag: StrPath = "images/notebooks.diag",
    nb_dir: StrPath = "notebooks",
    font: StrPath = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
) -> StrPath:
    with TemporaryDirectory() as workdir:
        skeleton = Path(workdir) / "skeleton.svg"
        _generate_skeleton(skeleton, Path(diag), Path(font))
        _embed_detail_information(Path(output), skeleton, Path(nb_dir))
        return output


def notebooks_toc(nb_dir: StrPath = "notebooks") -> str:
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


def setup_nb_workdir(work_dir: StrPath, nb_dir: StrPath = "notebooks") -> None:
    work = Path(work_dir)
    if not work.exists():
        work.mkdir(parents=True, exist_ok=True)
    for sub_dir in [
        str(Path(nb_dir) / "images"),
        "scripts",
        "template",
        "playbooks",
        "patches",
        "plugins",
        "docker",
    ]:
        dst_dir = (work / Path(sub_dir).name).resolve()
        src_dir = Path(sub_dir).resolve()
        if src_dir.exists() and not dst_dir.exists():
            dst_dir.symlink_to(src_dir, target_is_directory=True)
    dst_gvars = work / "group_vars"
    src_gvars = Path("group_vars")
    if src_gvars.exists() and not dst_gvars.exists():
        copytree(src_gvars, dst_gvars)


def generate_html_work_nbs(
    work_dir: StrPath,
    nb_pattern: str = DEFAULT_NB_PATTERN,
    nb_group: str = "notebooks",
    nb_dir: StrPath = "notebooks",
) -> str:
    nb_path = Path(nb_dir)
    nb_items = dict(
        (str(nb_path / nb), header["title"]["text"])
        for nb, header in _get_notebook_headers(nb_path, nb_pattern).items()
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


def copy_ref_notebook(src_nb: str, dest_dir: str, trusted: bool = False) -> None:
    dest_nb = _get_dest_nb_path(src_nb, dest_dir)
    copyfile(src_nb, dest_nb)
    if trusted:
        run(["jupyter", "trust", dest_nb], check=False)
    print(dest_nb)


def _get_dest_nb_path(src_nb_path: StrPath, dest_dir: StrPath) -> str:
    prefix = datetime.now().strftime("%Y%m%d")
    src = Path(src_nb_path)
    dest = Path(dest_dir)
    index = len(list(dest.glob(f"{prefix}*"))) + 1
    return str(dest / f"{prefix}_{index:0>2}_{src.name}")
