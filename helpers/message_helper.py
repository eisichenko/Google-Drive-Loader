class ConsoleColors:
    GREEN = '\033[92m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    WARNING = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(string):
    print(ConsoleColors.GREEN + ConsoleColors.BOLD + str(string) + ConsoleColors.END)


def print_fail(string):
    print(ConsoleColors.FAIL + ConsoleColors.BOLD + str(string) + ConsoleColors.END)


def print_cyan(string):
    print(ConsoleColors.CYAN + ConsoleColors.BOLD + str(string) + ConsoleColors.END)


def print_warning(string):
    print(ConsoleColors.WARNING + ConsoleColors.BOLD + str(string) + ConsoleColors.END)
