import calendar as calmod
import json
from datetime import date

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry

log = logger.get_logger()


def _calendar_html_for_month(diary: list[DiaryEntry], year: int, month: int) -> str:
    """指定年月のカレンダーHTMLを生成（サイドバー表示用）。"""
    # date -> (url, topic_count)
    date_to_url_and_count: dict[date, tuple[str, int]] = {}
    for diaryentry in diary:
        diarydate = date.fromisoformat(diaryentry.date)
        date_to_url_and_count[diarydate] = (
            f"/dates/{diaryentry.date}.html",
            len(diaryentry.topics),
        )

    dates_in_month: dict[date, tuple[str, int]] = {
        dt: val
        for dt, val in date_to_url_and_count.items()
        if dt.year == year and dt.month == month
    }

    def density_class(count: int) -> str:
        if count >= 6:
            return "density-3"
        if count >= 3:
            return "density-2"
        if count >= 1:
            return "density-1"
        return ""

    cal = calmod.Calendar(firstweekday=calmod.SUNDAY)
    weeks = cal.monthdayscalendar(year, month)

    html_str = f"<p>{month}月</p>"
    html_str += "<table>\n<tr>"
    for day in ["日", "月", "火", "水", "木", "金", "土"]:
        html_str += f"<th>{day}</th>"
    html_str += "</tr>\n"

    for week in weeks:
        html_str += "<tr>"
        for day in week:
            if day == 0:
                html_str += "<td></td>"
            else:
                thisdate = date(year, month, day)
                if thisdate in dates_in_month:
                    url, cnt = dates_in_month[thisdate]
                    cls = density_class(cnt)
                    cls_attr = f' class="{cls}"' if cls else ""
                    html_str += f'<td{cls_attr}><a href="{url}">{day}</a></td>'
                else:
                    html_str += f"<td>{day}</td>"
        html_str += "</tr>\n"
    html_str += "</table>\n"

    return html_str


def generate(diary_entries: list[DiaryEntry]):
    """カレンダーデータ(calendar_data.json)を出力する。"""
    log.info("🔄 カレンダーデータ (calendar_data.json) を生成中...")

    months = sorted(
        {
            (date.fromisoformat(entry.date).year, date.fromisoformat(entry.date).month)
            for entry in diary_entries
        }
    )

    calendars: dict[str, str] = {}
    for y, m in months:
        calendars[f"{y}-{m:02d}"] = _calendar_html_for_month(diary_entries, y, m)

    calendar_data = {
        "available_months": [f"{y}-{m:02d}" for y, m in months],
        "calendars": calendars,
    }

    output_path = f"{config.FILE_NAMES.OUTPUT_JSON_DIR_NAME}calendar_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(calendar_data, f, ensure_ascii=False)

    log.info(f"✅ calendar_data.json を {len(months)} ヶ月分生成しました！")
