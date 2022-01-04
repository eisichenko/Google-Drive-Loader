class ConsoleColors:
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    WARNING = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(string: str) -> None:
    print(ConsoleColors.GREEN + ConsoleColors.BOLD + str(string) + ConsoleColors.END)


def print_fail(string: str) -> None:
    print(ConsoleColors.FAIL + ConsoleColors.BOLD + str(string) + ConsoleColors.END)


def print_cyan(string: str) -> None:
    print(ConsoleColors.CYAN + ConsoleColors.BOLD + str(string) + ConsoleColors.END)


def print_warning(string: str) -> None:
    print(ConsoleColors.WARNING + ConsoleColors.BOLD + str(string) + ConsoleColors.END)


def size_to_string(size_in_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
        if abs(size_in_bytes) < 1024.0:
            return f"{size_in_bytes:3.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} YB"


def time_to_string(time: float) -> str:
    if time < 60:
        return f'{time: .2f}s'

    time = int(time)

    seconds = time % 60
    time = int(time / 60)

    minutes = time % 60
    time = int(time / 60)

    hours = time

    if hours == 0:
        return f'{str(minutes).zfill(2)}m:{str(seconds).zfill(2)}s'

    return f'{str(hours).zfill(2)}h:{str(minutes).zfill(2)}m:{str(seconds).zfill(2)}s'
