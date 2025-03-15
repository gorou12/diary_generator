import argparse

from diary_generator import config, generator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-cache", action="store_true", help="キャッシュを使用する")
    args = parser.parse_args()

    config.configuration.set_use_cache(args.use_cache)

    generator.generate_all()


if __name__ == "__main__":
    main()
