import re
import sys

__all__ = [
    'arabic2indic',
    'clean_name',
    'indic2arabic',
    'latex_escape',
    'log_debug',
    'log_warning',
    'new_lines_to_spaces',
    'xml_escape',
]


CHARS = {
    'tab': '\t',
    'space': ' ',
    'newline': '\n',
}


def log_debug(msg: str):
    print(msg, file=sys.stderr)


def log_warning(msg: str):
    print(msg, file=sys.stderr)


arabic2indic_mapping = str.maketrans('1234567890', '١٢٣٤٥٦٧٨٩٠')
indic2arabic_mapping = str.maketrans('١٢٣٤٥٦٧٨٩٠', '1234567890')


def arabic2indic(text: str) -> str:
    return str(text).translate(arabic2indic_mapping)


def indic2arabic(text: str) -> str:
    return str(text).translate(indic2arabic_mapping)


def xml_escape(text: str) -> str:
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')

    return text


def latex_escape(text: str) -> str:
    if text:
        text = re.sub(r'([#$%&~_^\\{}])', r'\\\1', text)
        text = re.sub(r'([\[\]])', r'{\1}', text)

    return text


def new_lines_to_spaces(text: str) -> str:
    return text.replace('\n', ' ').replace('\\\\', ' ')
