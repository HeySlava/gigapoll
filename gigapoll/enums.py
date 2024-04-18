from enum import StrEnum


class Modes(StrEnum):
    PLUS_MINUS = '1'


class Commands(StrEnum):
    START = 'start'
    HELP = 'help'
    NEWTEMPLATE = 'newtemplate'
    MYTEMPLATES = 'mytemplates'
