import os
import time


def main() -> None:
    token_set = bool(os.getenv("DISCORD_BOT_TOKEN"))
    print("[bot] Stage 0 placeholder service started")
    print(f"[bot] DISCORD_BOT_TOKEN set: {token_set}")

    # Keep container alive in Stage 0 without connecting to Discord yet.
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
