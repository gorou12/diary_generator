from diary_generator import html
from diary_generator.models import DiaryEntry


def set_content(_: DiaryEntry):
    html.sidebar_content = {}
