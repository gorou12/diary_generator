import calendar
from collections import OrderedDict
from datetime import date

from diary_generator import html
from diary_generator.models import DiaryEntry


def set_content(diary: list[DiaryEntry]):
    today = date.today()
    toyear = today.year
    tomonth = today.month

    html.sidebar_content["calendar"] = calendar_html(diary, toyear, tomonth)


def calendar_html(diary: list[DiaryEntry], year: int, month: int) -> str:
    available_dates: OrderedDict[date, str] = {}
    for diaryentry in diary:
        diarydate = date.fromisoformat(diaryentry.date)
        available_dates[diarydate] = f"/dates/{diaryentry.date}.html"

    dates_to_show = {  # 今月分のリスト
        dt: pg
        for dt, pg in available_dates.items()
        if dt.year == year and dt.month == month
    }

    # 月間カレンダー
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    weeks = cal.monthdayscalendar(year, month)

    html = f"<p>{month}月</p>"

    html += "<table>\n<tr>"
    for day in ["日", "月", "火", "水", "木", "金", "土"]:
        html += f"<th>{day}</th>"
    html += "</tr>\n"

    for week in weeks:
        html += "<tr>"
        for day in week:
            if day == 0:  # その月に存在しないマス
                html += "<td></td>"
            else:
                thisdate = date(year, month, day)
                html += (  # 記事があればリンク付き、なければ日付表示のみ
                    f'<td><a href="{dates_to_show[thisdate]}">{day}</td>'
                    if dates_to_show.get(thisdate)
                    else f"<td>{day}</td>"
                )
        html += "</tr>\n"
    html += "</table>\n"

    return html
