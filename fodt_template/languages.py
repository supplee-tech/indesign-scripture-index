# -*- coding: utf-8 -*-
import re
import sys
from typing import Optional
from gettext import gettext as _
from enum import Enum, unique

__all__ = [
    'Script',
    'ArabicScript',
    'GreekScript',
    'LatinScript',
    'HebrewScript',
    'Language',
    'ArabicLanguage',
    'EnglishLanguage',
    'GreekLanguage',
    'HebrewLanguage',

    'get_language',
    'get_script_class',

    'SCRIPTS',
    'LANGUAGES',
    'DIRECTIONS',
]


@unique
class SCRIPTS(Enum):
    ARABIC = 'ar'
    GREEK = 'el'
    HEBREW = 'he'
    LATIN = 'la'


@unique
class LANGUAGES(Enum):
    ARABIC = 'ar'
    ENGLISH = 'en'
    GREEK = 'el'
    HEBREW = 'he'


@unique
class DIRECTIONS(Enum):
    LTR = 'ltr'
    RTL = 'rtl'


class Script:
    _re_min: re.Pattern = None
    _re_max: re.Pattern = None
    _direction: DIRECTIONS = DIRECTIONS.LTR
    _code: SCRIPTS = None
    _name: str = None
    _char_class: str = None
    _punc_class: str = None
    _nums_class: str = None
    _conversions: dict = {}
    _conv_from: str = None
    _conv_to: str = None
    _conv_delete: str = None

    @classmethod
    def name(cls) -> str:
        return cls._name

    @classmethod
    def code(cls) -> str:
        return cls._code.value

    @classmethod
    def direction(cls) -> DIRECTIONS:
        return cls._direction

    @classmethod
    def token_min_regex(cls) -> re.Pattern:
        return cls._re_min

    @classmethod
    def token_max_regex(cls) -> re.Pattern:
        return cls._re_max

    @classmethod
    def re_char_class(cls) -> str:
        return cls._char_class

    @classmethod
    def re_punc_class(cls) -> str:
        return cls._punc_class

    @classmethod
    def has_script(cls, text: str) -> bool:
        if cls._re_min.search(text):
            return True

        return False

    @classmethod
    def is_script(cls, text: str) -> bool:
        if cls._re_max.search(text):
            return True

        return False

    @classmethod
    def tokenize(cls, text: str) -> list:
        results = []

        while True:
            match = cls._re_min.search(text)

            if match:
                if match.start(0):
                    results.append({'script_code': None, 'text': text[:match.start(0)]})

                results.append({'script_code': cls.code(), 'text': match.group('token')})

                text = text[match.end(0):]

            else:
                break

        if text:
            results.append({'script_code': None, 'text': text})

        return results

    @classmethod
    def is_text_script(cls, text: str) -> bool:
        return re.match(
            r'^[{chars}{punc}{nums}\s]*$'.format(
                chars=cls._char_class,
                punc=cls._punc_class,
                nums=cls._nums_class
            ),
            text
        ) is not None

    @classmethod
    def setup(cls):
        cls._conv_from = ''
        cls._conv_to = ''
        cls._conv_delete = ''
        for ltr in cls._conversions:
            for conv in cls._conversions[ltr]:
                if isinstance(conv, list):
                    for code in range(ord(conv[0]), ord(conv[1]) + 1):
                        if ltr is None:
                            cls._conv_delete += chr(code)
                        else:
                            cls._conv_from += chr(code)
                            cls._conv_to += ltr
                else:
                    if ltr is None:
                        cls._conv_delete += conv
                    else:
                        cls._conv_from += conv
                        cls._conv_to += ltr
        # print('conv_from:', cls._conv_from, file=sys.stderr)
        # print('conv_to:', cls._conv_to, file=sys.stderr)

    @classmethod
    def strip_text(cls, text: str) -> str:
        if cls._conv_from is None:
            cls.setup()

        if cls._conv_from:
            text = text.translate(str.maketrans(cls._conv_from, cls._conv_to))

        if cls._conv_delete:
            text = re.sub(r'[%s]+' % cls._conv_delete, '', text)

        text = re.sub(r'[%s]+' % cls._punc_class, ' ', text)
        text = re.sub(r'\s{2,}', ' ', text)

        return text.strip()


class ArabicScript(Script):
    _char_class = '\u0600-\u0605' \
                  '\u0608\u060B' \
                  '\u060D-\u061A' \
                  '\u061C-\u061E' \
                  '\u0620-\u065F' \
                  '\u066B' \
                  '\u066E-\u06DC' \
                  '\u06DF-\u06E8' \
                  '\u06EA\u06FF' \
                  '\u0750-\u077F' \
                  '\u08A0-\u08FF' \
                  '\uFB50-\uFDFF' \
                  '\uFE70-\uFEFF' \
                  '©'
    _punc_class = r'؟\.،؛<>\)\(/:"!@#$٪\^&\*“”\-\*–'
    _nums_class = r'0-9٠١٢٣٤٥٦٧٨٩'

    _direction = DIRECTIONS.RTL
    _name = _('Arabic')
    _code = SCRIPTS.ARABIC
    _re_min = re.compile(
        r'(?P<token>[{chars}]([{chars}{punc}{nums}\s]*[{chars}]|))'.format(
            chars=_char_class,
            punc=_punc_class,
            nums=_nums_class,
        )
    )
    _re_max = re.compile(
        r'(?P<token>[{punc}]*[{chars}]([{chars}{punc}{nums}\s]*[{chars}{punc}{nums}]|))'.format(
            chars=_char_class,
            punc=_punc_class,
            nums=_nums_class,
        )
    )
    # _replacements = {
    #     '\u'
    # }
    _conversions = {
        "\u0627": [  # Alef
            ['\u0622', '\u0623'],
            '\u0625',
            ['\u0671', '\u0673'],
            '\u0675',
        ],
        "\u0648": [  # Waw
            '\u0624',  # waw bil-hamza
            '\u066f',
            '\u0676',
            '\u0677',
            ['\u06c4', '\u06cb'],
            '\u06cf',
        ],
        "\u064a": [  # Ya'
            # '\u0626',
            '\u0649',
            ['\u06cc', '\u06ce'],
            ['\u06d0', '\u06d3'],
        ],
        ' ': [
            ['\u2010', '\u2015'],
            '\u061b',
            '\u066b',
            '\u066c',
        ],
        None: [
            '\u200e',
            '\u200f',
            ['\u202a', '\u202e'],
            ['\u064b', '\u064f'],
            ['\u0650', '\u065f'],
            '\u060c',
            '\u061b',
            '\u061f',
            '\u0670',
        ],
    }


class GreekScript(Script):
    _char_class = ('\u0370-\u03ff'
                   '\u1D26-\u1D2A'
                   '\u1d5d-\u1d6a'
                   '\u1dbf'
                   '\u1f00-\u1fff'
                   '\u0301'
                   '\u0313'
                   '\u0342'
                   '\u0345'
                   '\u0398'
                   )
    _punc_class = r'\.!,?;:@#\(\)%%&\-/\$\'"'
    _nums_class = r'0-9'

    _direction = DIRECTIONS.LTR
    _name = _('Greek')
    _code = SCRIPTS.GREEK
    _re_min = re.compile(
        r'(?P<token>[{chars}]([{chars}{punc}{nums}\s]*[{chars}]|))'.format(
            chars=_char_class,
            punc=_punc_class,
            nums=_nums_class,
        )
    )
    _re_max = re.compile(
        r'(?P<token>[{chars}]([{chars}{punc}{nums}\s]*[{chars}{punc}{nums}]|))'.format(
            chars=_char_class,
            punc=_punc_class,
            nums=_nums_class,
        )
    )


class HebrewScript(Script):
    _char_class = r'\u0590-\u05ff'
    _punc_class = r'؟\.،<>\)\(/:"!@#$٪\^&\*'
    _nums_class = r'0-9'

    _direction = DIRECTIONS.RTL
    _name = _('Hebrew')
    _code = SCRIPTS.HEBREW
    _re_min = re.compile(
        r'(?P<token>[{chars}]([{chars}{punc}{nums}\s]*[{chars}]|))'.format(
            chars=_char_class,
            punc=_punc_class,
            nums=_nums_class,
        )
    )
    _re_max = re.compile(
        r'(?P<token>[{chars}]([{chars}{punc}{nums}\s]*[{chars}{punc}{nums}]|))'.format(
            chars=_char_class,
            punc=_punc_class,
            nums=_nums_class,
        )
    )
    _conversions = {
        '\u05d0': [
            '\ufb20',
            '\ufb21',
            '\ufb2e',
            '\ufb2f',
            '\ufb30',
        ],
        '\u05d1': [
            '\ufb31',
        ],
        '\u05d2': [
            '\ufb32',
        ],
        '\u05d3': [
            '\ufb33',
        ],
        '\u05d4': [
            '\ufb34',
        ],
        '\u05d5': [
            '\ufb35',
            '\ufb4b',
        ],
        '\u05d6': [
            '\ufb36',
        ],
        '\u05d7': [
            '\ufb37',
        ],
        '\u05d8': [
            '\ufb38',
        ],
        '\u05d9': [
            '\ufb39',
        ],
        '\u05da': [
            '\ufb3a',
        ],
        '\u05db': [
            '\ufb3b',
        ],
        '\u05dc': [
            '\ufb3c',
        ],
        '\u05dd': [
            '\ufb3d',
        ],
        '\u05de': [
            '\ufb3e',
        ],
        '\u05df': [
            '\ufb3f',
        ],
        '\u05e0': [
            '\ufb40',
        ],
        '\u05e1': [
            '\ufb41',
        ],
        '\u05e2': [
            '\ufb42',
        ],
        '\u05e3': [
            '\ufb43',
        ],
        '\u05e4': [
            '\ufb44',
        ],
        '\u05e5': [
            '\ufb45',
        ],
        '\u05e6': [
            '\ufb46',
        ],
        '\u05e7': [
            '\ufb47',
        ],
        '\u05e8': [
            '\ufb48',
        ],
        '\u05e9': [
            '\ufb49',
            ['\ufb2a', '\ufb2d']
        ],
        ' ': [
            '\u05c0',
            '\u05be',
        ],
        None: [
            ['\u0590', '\u05c5'],
            '\u05c7',
            '\u0323',
            '\ufeff',
            '\u200c',
            '\u200d',
        ]
    }


class LatinScript(Script):
    _char_class = r'A-Za-z©'
    _punc_class = r'\.!,?;:@#\(\)%%&\-/\$\'’"“”–\*–'
    _nums_class = r'0-9'
    _direction = DIRECTIONS.LTR
    _name = _('Latin')
    _code = SCRIPTS.LATIN
    _re_min = re.compile(
        r'(?P<token>[{chars}]([{chars}{punc}{nums}\s]*[{chars}]|))'.format(
            chars=_char_class,
            punc=_punc_class,
            nums=_nums_class,
        )
    )
    _re_max = re.compile(
        r'(?P<token>[{punc}]*[{chars}]([{chars}{punc}{nums}\s]*[{chars}{punc}{nums}]|))'.format(
            chars=_char_class,
            punc=_punc_class,
            nums=_nums_class,
        )
    )


class Language:
    _direction: str = DIRECTIONS.LTR
    _code: LANGUAGES = None
    _name: str = None
    _script: Script = None
    _verse_delim: str = None
    _polyglossia_environment: str = None

    @classmethod
    def name(cls) -> str:
        return cls._name

    @classmethod
    def code(cls) -> str:
        return cls._code.value

    @classmethod
    def direction(cls) -> str:
        return cls._direction

    @classmethod
    def script(cls) -> Script:
        return cls._script

    @classmethod
    def verse_delim(cls):
        return cls._verse_delim

    @classmethod
    def polyglossia_environment(cls) -> str:
        return cls._polyglossia_environment


class ArabicLanguage(Language):
    _direction = DIRECTIONS.RTL
    _code = LANGUAGES.ARABIC
    _name = _('Arabic')
    _script = ArabicScript
    _verse_delim = '،'
    _polyglossia_environment = 'Arabic'


class EnglishLanguage(Language):
    _direction = DIRECTIONS.LTR
    _code = LANGUAGES.ENGLISH
    _name = _('English')
    _script = LatinScript
    _verse_delim = ','
    _polyglossia_environment = 'english'


class GreekLanguage(Language):
    _direction = DIRECTIONS.LTR
    _code = LANGUAGES.GREEK
    _name = _('Greek')
    _script = GreekScript
    _verse_delim = ','
    _polyglossia_environment = 'greek'


class HebrewLanguage(Language):
    _direction = DIRECTIONS.RTL
    _code = LANGUAGES.HEBREW
    _name = _('Hebrew')
    _script = HebrewScript
    _verse_delim = ','
    _polyglossia_environment = 'hebrew'


def get_language(code: str) -> Optional[Language]:
    if code.lower() == ArabicLanguage.code() or code.title() == ArabicLanguage.name():
        return ArabicLanguage()

    elif code.lower() == EnglishLanguage.code() or code.title() == EnglishLanguage.name():
        return EnglishLanguage()

    elif code.lower() == HebrewLanguage.code() or code.title() == HebrewLanguage.name():
        return HebrewLanguage()

    elif code.lower() == GreekLanguage.code() or code.title() == GreekLanguage.name():
        return GreekLanguage()

    return None


def get_script_class(script: SCRIPTS):
    if script == SCRIPTS.GREEK:
        return GreekScript
    elif script == SCRIPTS.HEBREW:
        return HebrewScript
    elif script == SCRIPTS.ARABIC:
        return ArabicScript

    return LatinScript
