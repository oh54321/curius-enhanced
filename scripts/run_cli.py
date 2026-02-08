import os
import sys

from src.cli.app import CuriusCLI

ENV_KEYS = ("CURIUS_START_USER_LINK", "CURIUS_USER_LINK")


def _get_start_user_link(argv: list[str]) -> str:
    if len(argv) > 1 and argv[1].strip():
        return argv[1].strip()

    for key in ENV_KEYS:
        env_value = os.getenv(key)
        if env_value and env_value.strip():
            return env_value.strip()

    while True:
        name = input("Enter start user name: ").strip()
        if name:
            return name
        print("Name cannot be empty. Please try again.")


def main() -> int:
    try:
        start_user_link = _get_start_user_link(sys.argv)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    os.environ["CURIUS_START_USER_LINK"] = start_user_link
    app = CuriusCLI(start_user_link)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
