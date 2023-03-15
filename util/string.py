import re


CAMEL_TO_SNAKE_REGEX = r'(?<!^)(?=[A-Z])'


def camel_to_snake(string: str) -> str:
    name = re.sub(CAMEL_TO_SNAKE_REGEX, '_', string).lower()
    name = name.replace(' ', '')
    return name


def snake_to_camel(string: str) -> str:
    return ''.join(word.title() for word in string.split('_'))


def snake_to_english(string: str) -> str:
    return ' '.join(word.title() for word in string.split('_'))


def camel_to_english(string: str) -> str:
    name = ""
    for prev_char, next_char in zip(string[:-1], string[1:]):
        name += prev_char
        if prev_char == prev_char.lower() and next_char == next_char.upper():
            name += " "
    name += next_char
    return name


def fmt_to_excel_title(string: str) -> str:
    """
    Replace spaces with %20
    """
    return string.replace(' ', '%20')


def fmt_to_field(string: str) -> str:
    """
    Remove all spaces, switch to snake case, remove all dashes
    """
    string = string.lower()
    string = string.replace(' ', '_')
    string = string.replace('-', '_')
    return string
