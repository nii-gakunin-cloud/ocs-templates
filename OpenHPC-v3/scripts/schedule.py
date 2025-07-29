# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0

import calendar
import json
import locale
import os
import re
import subprocess
from locale import LC_TIME, setlocale
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypeAlias, TypedDict, cast

from group import load_group_var

CMD_SCHEDULE_UTILS = ".venv/bin/vcp-schedule-utils"


class DailySchedule(TypedDict):
    hour: int
    minute: int


class WeeklySchedule(DailySchedule):
    day_of_week: int


class MonthlySchedule(DailySchedule):
    day: int


class YearlySchedule(MonthlySchedule):
    month: int


class SpecificDateSchedule(YearlySchedule):
    year: int


Schedule: TypeAlias = (
    DailySchedule | WeeklySchedule | MonthlySchedule | YearlySchedule | SpecificDateSchedule
)


class DailyPeriod(TypedDict):
    begin: DailySchedule
    end: DailySchedule


class WeeklyPeriod(TypedDict):
    begin: WeeklySchedule
    end: WeeklySchedule


class MonthlyPeriod(TypedDict):
    begin: MonthlySchedule
    end: MonthlySchedule


class YearlyPeriod(TypedDict):
    begin: YearlySchedule
    end: YearlySchedule


class SpecificDatePeriod(TypedDict):
    begin: SpecificDateSchedule
    end: SpecificDateSchedule


Period: TypeAlias = DailyPeriod | WeeklyPeriod | MonthlyPeriod | YearlyPeriod | SpecificDatePeriod


TIME_PATTERN = re.compile(r"( [012]? \d ) \s* : \s* ( [0-5]? \d )", re.X)
WEEKLY_PATTERN = re.compile(
    r"""(
        [日月火水木金土](?:曜日)?
        | (?:Sun|Mon|Tue|Wed|Thu|Fri|Sat)
        | (?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)
        ) \s* 
        ( [012]? \d ) \s* : \s* ( [0-5]? \d )
    """,
    re.X | re.I,
)
MONTHLY_PATTERN = re.compile(
    r"""
        ( [0-3]? \d )
        (?: 日\s* | \s+ )
        ( [012]? \d ) \s* : \s* ( [0-5]? \d )
    """,
    re.X,
)
YEARLY_PATTERN = re.compile(
    r"""
        (?:
            ( [012]? \d ) \s* / \s* ( [0-3]? \d )
            | ( [012]? \d ) \s* 月 \s* ( [0-3]? \d ) \s* 日
        )
        \s*
        ( [012]? \d ) \s* : \s* ( [0-5]? \d )
    """,
    re.X,
)
SPECIFIC_DATE_PATTERN = re.compile(
    r"""
        (?:
            ( \d{4} ) \s* / \s* ( [012]? \d ) \s* / \s* ( [0-3]? \d )
            | ( \d{4} ) \s* 年 \s* ( [012]? \d ) \s* 月 \s* ( [0-3]? \d ) \s* 日
        )
        \s*
        ( [012]? \d ) \s* : \s* ( [0-5]? \d )
    """,
    re.X,
)


class Weekday:
    def __init__(self):
        self._daynames = Weekday._get_daynames()

    @staticmethod
    def _get_daynames():
        daynames = {}
        setlocale(LC_TIME, None)
        daynames["name-en"] = list(calendar.day_name)
        daynames["abbr-en"] = list(calendar.day_abbr)
        try:
            setlocale(LC_TIME, "ja_JP.UTF-8")
            daynames["name-ja"] = list(calendar.day_name)
            daynames["abbr-ja"] = list(calendar.day_abbr)
        except locale.Error:
            daynames["name-ja"] = [
                "月曜日",
                "火曜日",
                "水曜日",
                "木曜日",
                "金曜日",
                "土曜日",
                "日曜日",
            ]
            daynames["abbr-ja"] = ["月", "火", "水", "木", "金", "土", "日"]

        setlocale(LC_TIME, None)
        return daynames

    def to_weekday(self, txt: str) -> int:
        txt = txt.capitalize()
        for labels in self._daynames.values():
            for i, label in enumerate(labels):
                if txt == label:
                    return (i + 1) % 7
        msg = f"Invalid weekday: {txt}"
        raise ValueError(msg)

    def to_text(self, weekday: int, lang: str = "ja") -> str:
        weekday = v if (v := weekday - 1) >= 0 else 6
        try:
            return self._daynames[f"name-{lang}"][weekday]
        except KeyError as e:
            msg = f"Invalid language: {lang}"
            raise ValueError(msg) from e
        except IndexError as e:
            msg = f"Invalid weekday: {weekday}"
            raise ValueError(msg) from e


WEEKDAY = Weekday()


class OcsNodeSchedule(TypedDict):
    node_count: int
    period: Period


class NodeDefaultParams(TypedDict):
    node_count: int
    max_node_count: int
    down_type: str
    drain_time: int


class OcsScheduleDefinition(TypedDict):
    default: NodeDefaultParams
    schedule: list[OcsNodeSchedule]


def _to_schedule(txt: str) -> Schedule:
    txt = txt.strip()
    if m := SPECIFIC_DATE_PATTERN.match(txt):
        return SpecificDateSchedule(
            year=int(m.group(1) or m.group(4)),
            month=int(m.group(2) or m.group(5)),
            day=int(m.group(3) or m.group(6)),
            hour=int(m.group(7)),
            minute=int(m.group(8)),
        )
    if m := YEARLY_PATTERN.match(txt):
        return YearlySchedule(
            month=int(m.group(1) or m.group(3)),
            day=int(m.group(2) or m.group(4)),
            hour=int(m.group(5)),
            minute=int(m.group(6)),
        )
    if m := MONTHLY_PATTERN.match(txt):
        return MonthlySchedule(day=int(m.group(1)), hour=int(m.group(2)), minute=int(m.group(3)))
    if m := WEEKLY_PATTERN.match(txt):
        return WeeklySchedule(
            day_of_week=WEEKDAY.to_weekday(m.group(1)), hour=int(m.group(2)), minute=int(m.group(3))
        )
    if m := TIME_PATTERN.match(txt):
        return DailySchedule(hour=int(m.group(1)), minute=int(m.group(2)))

    msg = f"スケジュールの指定文字列に誤りがある: {txt}"
    raise ValueError(msg)


def _to_period(begin_txt: str, end_txt: str):
    begin = _to_schedule(begin_txt)
    end = _to_schedule(end_txt)
    if "year" in begin or "year" in end:
        if "year" not in begin or "year" not in end:
            msg = f"開始と終了に指定したスケジュールの粒度が異なります: {begin_txt} - {end_txt}"
            raise ValueError(msg)
        return SpecificDatePeriod(
            begin=cast(SpecificDateSchedule, begin), end=cast(SpecificDateSchedule, end)
        )
    if "month" in begin or "month" in end:
        if "month" not in begin or "month" not in end:
            msg = f"開始と終了に指定したスケジュールの粒度が異なります: {begin_txt} - {end_txt}"
            raise ValueError(msg)
        return YearlyPeriod(begin=cast(YearlySchedule, begin), end=cast(YearlySchedule, end))
    if "day" in begin or "day" in end:
        if "day" not in begin or "day" not in end:
            msg = f"開始と終了に指定したスケジュールの粒度が異なります: {begin_txt} - {end_txt}"
            raise ValueError(msg)
        return MonthlyPeriod(begin=cast(MonthlySchedule, begin), end=cast(MonthlySchedule, end))
    if "day_of_week" in begin or "day_of_week" in end:
        if "day_of_week" not in begin or "day_of_week" not in end:
            msg = f"開始と終了に指定したスケジュールの粒度が異なります: {begin_txt} - {end_txt}"
            raise ValueError(msg)
        return WeeklyPeriod(begin=cast(WeeklySchedule, begin), end=cast(WeeklySchedule, end))
    return DailyPeriod(begin=cast(DailySchedule, begin), end=cast(DailySchedule, end))


def get_schedule(params: dict) -> list[OcsNodeSchedule]:
    if "schedule_list" not in params:
        return []
    schedules: list[OcsNodeSchedule] = []
    for item in params["schedule_list"]:
        begin_txt = item.get("begin")
        end_txt = item.get("end")
        nodes_txt = item.get("node_count")
        schedule = OcsNodeSchedule(node_count=int(nodes_txt), period=_to_period(begin_txt, end_txt))
        schedules.append(schedule)
    return schedules


def _get_default_node_count(ugroup_name: str, params: dict) -> int:
    if "schedule_default_compute_nodes" in params:
        return int(params["schedule_default_compute_nodes"])
    value = load_group_var(ugroup_name, "compute_nodes")
    return int(value) if value is not None else 0


def _get_max_compute_nodes(ugroup_name: str) -> int:
    value = load_group_var(ugroup_name, "max_compute_nodes")
    if value is not None:
        return int(value)
    msg = f"max_compute_nodes is not defined in {ugroup_name}"
    raise ValueError(msg)


def _get_down_type(params: dict) -> str:
    if "schedule_down_type" in params:
        return params["schedule_down_type"]
    msg = "schedule_down_type is not defined"
    raise ValueError(msg)


def _get_drain_time(params: dict) -> int:
    if "schedule_drain_time" in params:
        return int(params["schedule_drain_time"])
    return 0


def _get_default_params(ugroup_name: str, params: dict) -> NodeDefaultParams:
    return {
        "node_count": _get_default_node_count(ugroup_name, params),
        "max_node_count": _get_max_compute_nodes(ugroup_name),
        "down_type": _get_down_type(params),
        "drain_time": _get_drain_time(params),
    }


def _get_schedule_definition(ugroup_name: str, params: dict | None = None) -> OcsScheduleDefinition:
    if params is None:
        cfg = load_group_var(ugroup_name, "vcnode_schedule")
        if cfg is None:
            msg = f"vcnode_schedule is not defined in {ugroup_name}"
            raise ValueError(msg)
        return cfg

    return {
        "default": _get_default_params(ugroup_name, params),
        "schedule": get_schedule(params),
    }


def _check_schedule_definition(cfg: OcsScheduleDefinition) -> None:
    max_count = cfg["default"]["max_node_count"]
    if max_count <= 0:
        msg = "最大計算ノード数(max_node_count)は1以上である必要があります"
        raise ValueError(msg)
    if cfg["default"]["node_count"] < 0:
        msg = "通常時の計算ノード数は0以上である必要があります"
        raise ValueError(msg)
    if cfg["default"]["node_count"] > max_count:
        msg = "通常時の計算ノード数は最大計算ノード数以下である必要があります"
        raise ValueError(msg)
    if "drain_time" in cfg["default"] and cfg["default"]["drain_time"] < 0:
        msg = "DRAIN状態とする時間drain_timeは0以上である必要があります"
        raise ValueError(msg)
    if cfg["default"]["down_type"] not in ["power_down", "deleted"]:
        msg = "停止時のノード状態down_typeはpower_downまたはdeletedである必要があります"
        raise ValueError(msg)

    for schedule in cfg["schedule"]:
        if schedule["node_count"] < 0:
            msg = "計算ノード数は0以上である必要があります"
            raise ValueError(msg)
        if schedule["node_count"] > max_count:
            msg = "計算ノード数は最大計算ノード数以下である必要があります"
            raise ValueError(msg)


def get_schedule_definition(ugroup_name: str, params: dict | None = None) -> OcsScheduleDefinition:
    cfg = _get_schedule_definition(ugroup_name, params)
    _check_schedule_definition(cfg)
    return cfg


def description_schedule(
    ugroup_name: str, params: dict | None = None, desc_type: str = "all"
) -> None:
    with TemporaryDirectory() as work_dir:
        cfg_path = Path(work_dir) / "schedule.json"
        cfg = get_schedule_definition(ugroup_name, params)
        with cfg_path.open(mode="w", encoding="utf-8") as f:
            json.dump(cfg, f)
        if "TZ" in os.environ:
            del os.environ["TZ"]
        subprocess.run(
            [CMD_SCHEDULE_UTILS, "-D", "-c", str(cfg_path), "--desc-type", desc_type], check=True
        )


def _schedule_to_txt(schedule: Schedule, lang: str) -> str:
    if "year" in schedule:
        sds: SpecificDateSchedule = cast(SpecificDateSchedule, schedule)
        return f"{sds['year']}/{sds['month']}/{sds['day']} {sds['hour']}:{sds['minute']:02}"
    if "month" in schedule:
        ys: YearlySchedule = cast(YearlySchedule, schedule)
        return f"{ys['month']}/{ys['day']} {ys['hour']}:{ys['minute']:02}"
    if "day" in schedule:
        ms: MonthlySchedule = cast(MonthlySchedule, schedule)
        if lang == "ja":
            return f"{ms['day']}日 {ms['hour']}:{ms['minute']:02}"
        return f"{ms['day']} {ms['hour']}:{ms['minute']:02}"
    if "day_of_week" in schedule:
        ws: WeeklySchedule = cast(WeeklySchedule, schedule)
        return f"{WEEKDAY.to_text(ws['day_of_week'], lang)} {ws['hour']}:{ws['minute']:02}"
    ds: DailySchedule = cast(DailySchedule, schedule)
    return f"{ds['hour']}:{ds['minute']:02}"


def get_schedule_list(ugroup_name: str, lang: str = "ja") -> list[dict]:
    cfg = load_group_var(ugroup_name, "vcnode_schedule")
    if cfg is None or not isinstance(cfg, dict) or "schedule" not in cfg:
        msg = f"schedule is not defined in {ugroup_name}"
        raise ValueError(msg)
    schedules = [
        {
            "begin": _schedule_to_txt(item["period"]["begin"], lang),
            "end": _schedule_to_txt(item["period"]["end"], lang),
            "node_count": item["node_count"],
        }
        for item in cfg["schedule"]
    ]
    return schedules


def show_schedule_list(ugroup_name: str, lang: str = "ja") -> None:
    schedules = get_schedule_list(ugroup_name, lang)
    print(json.dumps(schedules, indent=4, ensure_ascii=False))
