from dataclasses import dataclass
import re
from colorama import Fore


# [*] Patterns
CACHE_GRAB_PATTERN = re.compile("c[0-9]+:[0-9]+[el]:[0-9]+:[0-9]+:[rlbn]")
INTEGER_PATTERN = re.compile("[0-9]+")
FLOAT_PATTERN = re.compile(r"[0-9]+\.[0-9]+")


RECOGNIZED_KEYWORDS = {'&RUN', '&SAFECIN', '&SUM', '&SET', '&SUB', '&FILE.EXISTS', '&CLEAR', '&DIR.EXISTS', '&BACK', '&PATH.EXISTS', '&ECHO', '&STYLE', '&RESET', '&REQUIRES', '&CIN', '&YAYORNAY', '&ENDL2', '&COUT', '&REQINSTALL', '&ENDL', '&REM', '&GETPASS', '&ABS', '&INVERT', '&PKGRUN', '&ROUND', '&DIV', '&FORE', '&PIPRUN', '&NPMRUN', '&TERMINATE', '&ECHORDIE',
                       '!INVERT', '!PATH.EXISTS', '!FILE.EXISTS', '!DIR.EXISTS', '!RESET', '!SUM', '!REM', '!DIV', '!SUB', '!ABS', '!ROUND', '!PROD', '!ENDL', '!ENDL2', '!GETPASS', '!COUT', '!ECHO', '!CIN', '!TERMINATE', '!REQUIRES', '!REQINSTALL', '!STYLE', '!FORE', '!BACK', '!CLEAR', '!SET', '!ECHORDIE', '!SAFECIN', '!YAYORNAY', '!PKGRUN', '!RUN', '!PIPRUN', '!NPMRUN',
                       'INVERT', 'PATH.EXISTS', 'FILE.EXISTS', 'DIR.EXISTS', 'RESET', 'SUM', 'REM', 'DIV', 'SUB', 'ABS', 'ROUND', 'PROD', 'ENDL', 'ENDL2', 'GETPASS', 'COUT', 'ECHO', 'CIN', 'TERMINATE', 'REQUIRES', 'REQINSTALL', 'STYLE', 'FORE', 'BACK', 'CLEAR', 'SET', 'ECHORDIE', 'SAFECIN', 'YAYORNAY', 'PKGRUN', 'RUN', 'PIPRUN', 'NPMRUN'}
PARTS_PER_KEYWORD: dict[str, int | tuple[int, int] | tuple[int, int, int]] = {
    'ABS':                      1,
    'BACK':                     1,
    'CIN':                      (0, 1, 2),
    'CLEAR':                    1,
    'COUT':                     -1,
    'DIR.EXISTS':               1,
    'DIV':                      2,
    'ECHO':                     2,
    'ECHORDIE':                 2,
    'ENDL':                     0,
    'ENDL2':                    0,
    'FILE.EXISTS':              1,
    'FORE':                     1,
    'GETPASS':                  1,
    'INVERT':                   0,
    'NPMRUN':                   -1,
    'PATH.EXISTS':              1,
    'PIPRUN':                   -1,
    'PKGRUN':                   -1,
    'REM':                      2,
    'REQINSTALL':               0,
    'REQUIRES':                 2,
    'RESET':                    0,
    'ROUND':                    2,
    'RUN':                      -1,
    'SAFECIN':                  (1, 2),
    'SET':                      1,
    'STYLE':                    1,
    'SUB':                      2,
    'SUM':                      -1,
    'TERMINATE':                (0, 1, 2),
    'YAYORNAY':                 0
}


@dataclass
class Issue:
    line: int
    statement: int
    code: str
    message: str
    severity: int
    color: str

    def __str__(self) -> str:
        return f"[LINT] Line {self.line}: Global Statement {self.statement}: {self.code}: {self.message}"

    def as_pretty(self) -> str:
        return f"{Fore.LIGHTWHITE_EX}[LINT] {Fore.RESET}Line {Fore.MAGENTA}{self.line}{Fore.RESET}: Global Statement {Fore.MAGENTA}{self.statement}{Fore.RESET}: {self.color}{self.code}: {self.message}{Fore.RESET}"

    def as_json(self) -> dict[str, int | str]:
        return {
            "line": self.line,
            "statement": self.statement,
            "code": self.code,
            "message": self.message,
            "severity": self.severity # [i] starts at 1, cuz 0 is "Nothing to report"
        }

    def as_tuple(self) -> tuple[int, int, str, str, int]:
        return (self.line, self.statement, self.code, self.message, self.severity)


class ErrorCheckers:
    @staticmethod
    def e001_semicolon(line: str, lineno: int, ignore_list: list[str]) -> Issue | None:
        """
        E001 - Missing semicolon at the end of the line
        -----------------------
        ### Example
        ```cxsetup
        COUT ?? 42
        ```
        ### Instead, do:
        ```cxsetup
        COUT ?? 42;
        ```
        """

        if "E001" in ignore_list:
            return # [i] pretend nothing happened

        if lineno == 0 and re.fullmatch(INTEGER_PATTERN, line):
            return

        if "//" in line:
            return

        if not line.endswith(';'):
            return Issue(lineno + 1, -1, "E001", "Missing semicolon at the end of the line", 3, Fore.RED)

        return

    @staticmethod
    def e002_unknown_keyword(statement: str, lineno: int, statement_no: int, ignore_list: list[str]) -> Issue | None:
        """
        E002 - Unknown Keyword
        -----------------------
        ### Example
        ```cxsetup
        FOOBAR ?? "Hello!";
        ```

        ### Explanation
        - `FOOBAR` is not a recognized keyword
        """

        if "E002" in ignore_list:
            return

        if lineno == 0 and re.fullmatch(INTEGER_PATTERN, statement):
            return

        if statement.split('??', maxsplit=1)[0].strip().endswith(';'):
            if statement.split('??', masplit=1)[0][:-1].strip() not in RECOGNIZED_KEYWORDS:
                return Issue(lineno, statement_no, "E002", f"Unknown Keyword {statement.split('??', masplit=1)[0][:-1].strip()}", 3, Fore.RED)

            return

        if statement.split('??', masplit=1)[0].strip() not in RECOGNIZED_KEYWORDS:
            return Issue(lineno, statement_no, "E002", f"Unknown Keyword {statement.split('??', masplit=1)[0].strip()}", 3, Fore.RED)

        return

    @staticmethod
    def e003_arguments(statement: str, lineno: int, statement_no: int, ignore_list: list[str]):
        """
        E003 - Too many or too few arguments
        -----------------------
        ### Example
        ```cxsetup
        SET ?? 42 ?? 50;
        ```

        ### Explanation
        - SET has no overload that takes 2 arguments
        """

        if "E003" in ignore_list:
            return

        parts = statement.split('??')
        arg_counter = 0
        func = parts[0]

        if func.startswith(('!', '&', '+')):
            func = parts[0][1:]

        if func.endswith(';'):
            func = func[:-1]

        else:
            for index, part in enumerate(parts, 0):
                if '//' in part:
                    break

                if index == 0:
                    continue

                arg_counter += 1

        if func in PARTS_PER_KEYWORD:
            if PARTS_PER_KEYWORD[func] == -1:
                return

            if isinstance(PARTS_PER_KEYWORD[func], tuple):
                if arg_counter in PARTS_PER_KEYWORD:
                    return

                return Issue(lineno, statement_no, "E003", f"No overload of {func} takes {arg_counter} arguments", 3, Fore.RED)

            if PARTS_PER_KEYWORD[func] == arg_counter:
                return

            return Issue(lineno, statement_no, "E003", f"No overload of {func} takes {arg_counter} arguments", 3, Fore.RED)

        Issue(lineno, statement_no, "E003", f"Couldn't find an overload of {func} that takes {arg_counter} arguments", 3, Fore.RED)

    @staticmethod
    def e004_invalid_cxvar():
        # TODO
        return

class Linter:
    def __init__(self):
        self.ISSUES: list[Issue] = []

    def lint_code():
        # TODO
        return 0
