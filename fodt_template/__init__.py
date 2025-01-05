import re
import sys
from typing import Optional

__all__ = [
    'CHARS',

    'ANGLED_DOUBLE',
    'ANGLED_EXCLAMATION',
    'ANGLED_SINGLE',
    'BLOCK',
    'BOLD',
    'BOLD_ITALIC',
    'CODE',
    'CURLY_SINGLE',
    'DIVISION',
    'DIVISION_BREAK',
    'DOCUMENT',
    'ELLIPSIS',
    'HEADING',
    'IMAGE',
    'INDEX',
    'INDEX_DIVISION',
    'INDEX_ENTRY',
    'INDEX_HEADING',
    'INDEX_MARK',
    # 'INDEX_SUBITEM',
    'ITALIC',
    'LINEBREAK',
    'LINK',
    'LIST',
    'LIST_ITEM',
    'NODE',
    'NOTE',
    'NOTE_REFERENCE',
    'NUMBERS',
    'PAGEBREAK',
    'PARAGRAPH',
    'PARENTHESIS_SINGLE',
    'QUOTEBLOCK',
    'REFERENCE_MARK',
    'REFERENCE_REF',
    'SCRIPT',
    'SCRIPT_ARABIC',
    'SCRIPT_GREEK',
    'SCRIPT_HEBREW',
    'SCRIPT_LATIN',
    'SPACE',
    'SPAN',
    'SQUARE_DOUBLE',
    'SQUARE_SINGLE',
    'TAB',
    'TABLE',
    'TABLE_CELL',
    'TABLE_COLUMN',
    'TABLE_ROW',
    'TEXT',
    'TEXT_BLOCK',
    'VARIABLE',
    'VERSE_REFERENCE',
    'VERSE_REFERENCE_LIST',

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

ANGLED_DOUBLE = 'ANGLED_DOUBLE'
ANGLED_EXCLAMATION = 'ANGLED_EXCLAMATION'
ANGLED_SINGLE = 'ANGLED_SINGLE'
BLOCK = 'BLOCK'
BOLD = 'BOLD'
BOLD_ITALIC = 'BOLD_ITALIC'
CODE = 'CODE'
CURLY_SINGLE = 'CURLY_SINGLE'
DIVISION = 'DIVISION'
DIVISION_BREAK = 'DIVISION_BREAK'
DOCUMENT = 'DOCUMENT'
ELLIPSIS = 'ELLIPSIS'
HEADING = 'HEADING'
IMAGE = 'IMAGE'
INDEX = 'INDEX'
INDEX_DIVISION = 'DIVISION_INDEX'
INDEX_ENTRY = 'INDEX_ENTRY'
INDEX_HEADING = 'INDEX_HEADING'
INDEX_MARK = 'INDEX_MARK'
# INDEX_SUBITEM = 'INDEX_SUBITEM'
ITALIC = 'ITALIC'
LINEBREAK = 'LINEBREAK'
LINK = 'LINK'
LIST = 'LIST'
LIST_ITEM = 'LIST_ITEM'
NODE = 'NODE'
NOTE = 'NOTE'
NOTE_REFERENCE = 'NOTE_REFERENCE'
NUMBERS = 'NUMBERS'
PAGEBREAK = 'PAGEBREAK'
PARAGRAPH = 'PARAGRAPH'
PARENTHESIS_SINGLE = 'PARENTHESIS_SINGLE'
QUOTEBLOCK = 'QUOTEBLOCK'
REFERENCE_MARK = 'REFERENCE_MARK'
REFERENCE_REF = 'REFERENCE_REF'
SCRIPT_ARABIC = 'SCRIPT_ARABIC'
SCRIPT_GREEK = 'SCRIPT_GREEK'
SCRIPT_HEBREW = 'SCRIPT_HEBREW'
SCRIPT_LATIN = 'SCRIPT_LATIN'
SCRIPT = 'SCRIPT'
SPACE = 'SPACE'
SPAN = 'SPAN'
SQUARE_DOUBLE = 'SQUARE_DOUBLE'
SQUARE_SINGLE = 'SQUARE_SINGLE'
TAB = 'TAB'
TABLE = 'TABLE'
TABLE_CELL = 'TABLE_CELL'
TABLE_COLUMN = 'TABLE_COLUMN'
TABLE_ROW = 'TABLE_ROW'
TEXT = 'TEXT'
TEXT_BLOCK = 'TEXT_BLOCK'
VARIABLE = 'VARIABLE'
VERSE_REFERENCE = 'VERSE_REFERENCE'
VERSE_REFERENCE_LIST = 'VERSE_REFERENCE_LIST'


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


def clean_name(name: str) -> Optional[str]:
    if name is None:
        return None

    replacements = {
        '-': '_',
        ' ': '_',
        '(': '',  # '_28_',
        ')': '',  # '_29_',
    }

    name = re.sub(r'_(\d{2})_', lambda match: chr(int(match[1], 16)), name.lower())
    for key, value in replacements.items():
        name = name.replace(key, value)

    return name
