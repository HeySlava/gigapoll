from enum import StrEnum


class Modes(StrEnum):
    PLUS_MINUS = '1'


class Commands(StrEnum):
    START = 'start'
    HELP = 'help'
    NEWTEMPLATE = 'newtemplate'
    MYTEMPLATES = 'mytemplates'


class Prefix(StrEnum):
    VOTE = 'vote'
    MANAGER_LIST = 'man_list'
    DELETE_TEMPLATE = 'del_tpl'
