class ConfigKeyError(ValueError):
    pass


class PollModeError(ValueError):
    pass


class ConfigValueError(ValueError):
    pass


def parse_template(s: str) -> dict[str, str]:
    s = s.strip()
    conf = {}
    choices = []
    available_keys = ('name', 'version', 'mode',)
    available_modes = ('plus_minus',)
    for line in s.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith('-'):
            choice = line[1:]
            if choice:
                choices.append(choice)
                continue
            else:
                raise ValueError('Пустое значение для выбора')

        k, _, v = line.partition(':')
        k = k.strip()
        if k not in available_keys:
            raise ConfigKeyError(f'Unexpected key: {k!r}')
        v = v.strip()
        if not v:
            raise ConfigValueError("Value can't be empty")
        conf[k] = v

    for k in available_keys:
        if k not in conf:
            raise ConfigKeyError(f'Ключа {k!r} нет в введенном конфиге')

    mode = conf['mode']
    if mode not in available_modes:
        raise PollModeError(f'Мод {mode!r} не поддерживается')

    return conf
