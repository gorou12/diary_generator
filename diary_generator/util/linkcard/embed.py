import re


### Embed


def youtube(url):
    youtube_id_match = re.search(r"(?:v=|youtu.be/)([\w\-]+)", url)
    if not youtube_id_match:
        return f'<a href="{url}" target="_blank">{url}</a>'
    video_id = youtube_id_match.group(1)

    return f"""
    <div class="video-embed">
      <iframe width="100%" height="315"
        src="https://www.youtube.com/embed/{video_id}"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen>
      </iframe>
    </div>
    """


def niconico(url):
    nico_id_match = re.search(r"/watch/([a-z0-9]+)", url)
    if not nico_id_match:
        return f'<a href="{url}" target="_blank">{url}</a>'
    video_id = nico_id_match.group(1)

    return f"""
    <div class="video-embed">
      <iframe width="100%" height="315"
        src="https://embed.nicovideo.jp/watch/{video_id}"
        frameborder="0" allowfullscreen>
      </iframe>
    </div>
    """


def twitter(url):
    return f"""
    <blockquote class="twitter-tweet"><a href="{url}">{url}</a></blockquote>
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    """
