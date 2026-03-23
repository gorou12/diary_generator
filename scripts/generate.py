import argparse

from diary_generator import config, generator
from diary_generator.logger import logger

log = logger.get_logger()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-cache", action="store_true", help="キャッシュを使用する")
    parser.add_argument(
        "--use-topic-slug-cache",
        action="store_true",
        help="トピックスラッグキャッシュを使用する",
    )
    args = parser.parse_args()

    config.configuration.set_use_cache(args.use_cache)
    config.configuration.set_use_topic_slug_cache(args.use_topic_slug_cache)

    try:
        generator.generate_all()
    except Exception as e:
        log.error("生成処理を中断しました: %s", e)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
