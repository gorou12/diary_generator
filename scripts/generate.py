import argparse

from diary_generator import generator
from diary_generator.models.config import load_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-cache", action="store_true", help="キャッシュを使用する")
    args = parser.parse_args()

    config = load_config("config/settings.ini", "config/page.ini", args.use_cache)
    generator.generate_all(config)


if __name__ == "__main__":
    main()
