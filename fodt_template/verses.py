# -*- coding: utf-8 -*-
import re
import sys
from abc import ABCMeta, abstractmethod
# from dotted_dict import DottedDict
from dataclasses import dataclass, field
from enum import Enum, Flag, unique
from typing import Optional

from . import arabic2indic, indic2arabic, log_warning
from .bible_books import books_to_nums as _book_to_num
from .bible_books import nums_to_books as _num_to_book
from .bible_books import proper_book_names as _proper_book_names
from .languages import (DIRECTIONS, LANGUAGES, ArabicLanguage, ArabicScript,
                        EnglishLanguage, Language)

__all__ = [
    'book_to_number',
    'num_to_book',
    'VerseReference',
    'VerseReferenceList',
    'Marker',
    'parse_verse_reference',
    'ResultType',
    'BookNameNotFound',
    'BibleBooks',
    'InvalidVerseReference',
    'VerseStyle',
    'proper_books_names',
    'tokenize_text',
]


class BookNameNotFound(Exception):
    book_name: str
    text: str
    page: int

    def __init__(self, book_name, text_match: str = None, page: int = None):
        self.book_name = book_name
        self.text = text_match
        self.page = page
        book_hex = ':'.join([hex(ord(c)) for c in self.book_name])
        text_hex = ':'.join([hex(ord(c)) for c in indic2arabic(self.text if self.text else '')])
        super().__init__(f'{self.book_name} {book_hex} in {self.text} ({text_hex}) on page {self.page}')


class InvalidVerseReference(Exception):
    def __init__(self, ref_text: str):
        self.ref_text = ref_text
        super().__init__(self.ref_text)


class BibleBooks(Enum):
    GENESIS = 1
    EXODUS = 2
    LEVITICUS = 3
    NUMBERS = 4
    DEUTERONOMY = 5
    JOSHUA = 6
    JUDGES = 7
    RUTH = 8
    SAMUEL_1 = 9
    SAMUEL_2 = 10
    KINGS_1 = 11
    KINGS_2 = 12
    CHRONICLES_1 = 13
    CHRONICLES_2 = 14
    EZRA = 15
    NEHEMIAH = 16
    ESTHER = 17
    JOB = 18
    PSALMS = 19
    PROVERBS = 20
    ECCLESIASTES = 21
    SONG_OF_SONGS = 22
    ISAIAH = 23
    JEREMIAH = 24
    LAMENTATIONS = 25
    EZEKIEL = 26
    DANIEL = 27
    HOSEA = 28
    JOEL = 29
    AMOS = 30
    OBADIAH = 31
    JONAH = 32
    MICAH = 33
    NAHUM = 34
    HABAKKUK = 35
    ZEPHANIAH = 36
    HAGGAI = 37
    ZECHARIAH = 38
    MALACHI = 39

    MATTHEW = 40
    MARK = 41
    LUKE = 42
    JOHN = 43
    ACTS = 44
    ROMANS = 45
    CORINTHIANS_1 = 46
    CORINTHIANS_2 = 47
    GALATIANS = 48
    EPHESIANS = 49
    PHILIPPIANS = 50
    COLOSSIANS = 51
    THESSALONIANS_1 = 52
    THESSALONIANS_2 = 53
    TIMOTHY_1 = 54
    TIMOTHY_2 = 55
    TITUS = 56
    PHILEMON = 57
    HEBREWS = 58
    JAMES = 59
    PETER_1 = 60
    PETER_2 = 61
    JOHN_1 = 62
    JOHN_2 = 63
    JOHN_3 = 64
    JUDE = 65
    REVELATION = 66

    @classmethod
    def single_chapter_books(cls) -> tuple:
        return cls.OBADIAH, cls.PHILEMON, cls.JOHN_2, cls.JOHN_3, cls.JUDE


class VerseStyle(Enum):
    BRIEF = 'abbrev_title'
    FULL = 'full_title'
    STANDARD = 'title'
    TEXT = 'text'


# noinspection PyShadowingNames

def init():
    # global _num_to_book, _book_to_num
    for books in _num_to_book.values():
        for num, book in books.items():
            _book_to_num[book] = num
            _book_to_num[ArabicScript.strip_text(book)] = num


# init()


def book_to_number(book_name: str) -> int | None:
    # global _book_to_num
    book_name = indic2arabic(ArabicScript.strip_text(book_name))
    if book_name in _book_to_num:
        return _book_to_num[book_name]

    return None


def num_to_book(book_num: int, lang_code: str = 'en'):
    # global _num_to_book
    if lang_code in _num_to_book and str(book_num) in _num_to_book[lang_code]:
        return _num_to_book[lang_code][str(book_num)]

    # print('num_to_book:', book_num, lang_code, file=sys.stderr)
    # exit(1)
    return None


def proper_books_names(book_num: int, lang_code: str = 'en', style: VerseStyle = VerseStyle.STANDARD):
    # global _proper_book_names
    if lang_code in _proper_book_names and str(book_num) in _proper_book_names[lang_code]:
        return _proper_book_names[lang_code][str(book_num)][style.value]

    return None


class VerseReferenceAbstract(metaclass=ABCMeta):

    @abstractmethod
    def text(self, language: Language = EnglishLanguage, mime_type: str = 'html', style: str = None) -> str:
        pass

    # noinspection PyShadowingNames
    @abstractmethod
    def verse_formatted(self, lang: Language = EnglishLanguage) -> str:
        pass


class VerseReference(VerseReferenceAbstract):
    _re_verse = re.compile(r'\s*(?P<verse>\d+)\s*$')
    _re_book_chapter = re.compile(r'\s*(?P<book>\w+)\.(?P<chapter>\d+)\s*$')
    _re_book = re.compile(r'\s*(?P<book>\w+)\s*$')
    _ref_valid: bool = None

    parent: 'VerseReferenceList'
    order0: int = None
    ref_type: 'ResultType' = None
    book_prefix: str = None

    def __init__(self, ref: str = None, book: str = None, book_prefix: str = None,
                 chapter: str = None, verse: str = None,
                 authorities: list = None, **kwargs):
        super().__init__()
        self._authorities = []
        self._book = None
        self._book_num = None
        self._chapter = None
        self._verse = None
        self.set_book(book)
        self.book_prefix = book_prefix
        self.set_chapter(chapter)
        self.set_verse(verse)
        self._set_ref_text = None
        self._ref_valid = False
        self._is_marker = False
        self.text_before: str | None = None
        self.text_after: str | None = None
        self.text_book: str | None = None
        self.order0: int
        self.book_hidden: bool = False
        self.chapter_hidden: bool = False

        if authorities:
            self.set_authorities(authorities)
        if ref:
            self.set_ref_text(ref)
            self._ref_valid = self.parse_reference(ref)

    def __str__(self):
        return f'type: {self.ref_type}, book: {self.book()}, chapter: {self.chapter()},' \
            f' verse: {self.verse()}, bk hid: {self.book_hidden}, ch hid: {self.chapter_hidden}'

    def index(self) -> str:
        text = str(self.book_num()).rjust(2, '0')
        if self.chapter():
            text += '!' + str(self.chapter()).rjust(3, '0')
            if self.verse():
                text += ':' + re.sub(r'^\d+', lambda m: m[0].rjust(3, '0'), self.verse())

        return text

    def authorities(self):
        return self._authorities

    def has_authorities(self):
        return len(self._authorities) > 0

    def set_authorities(self, auths: list) -> None:
        self._authorities = auths

    @classmethod
    def factory(cls, ref: str) -> Optional['VerseReference']:
        vr = cls(ref=ref)
        if vr.is_valid():
            return vr

        return None

    def copy(self, vr: 'VerseReference'):
        self.ref_type = vr.ref_type
        self.set_authorities(vr.authorities())
        self.set_book(vr.book())
        self.set_book_num(vr.book_num())
        self.set_chapter(vr.chapter())
        self.set_verse(vr.verse())
        self.text_book = vr.text_book
        self.text_before = vr.text_before
        self.text_after = vr.text_after
        self.book_hidden = vr.book_hidden
        self.chapter_hidden = vr.chapter_hidden
        self._ref_valid = vr.is_valid()
        self.set_ref_text(vr._set_ref_text)  # pylint: disable=protected-access

    def parse_reference(self, ref: str) -> bool:
        result = parse_verse_reference(ref)

        if result.found and result.type in ResultType.ANY_REF:
            vr = result.verse_factory()
            self.copy(vr)
            self.set_ref_text(ref)
            self.ref_type = result.type

            return True

        return False

    def book(self) -> str:
        if not self._book and self.order0 is not None and self.order0 > 0:
            return self.parent[self.order0 - 1].book()

        return self._book

    def set_book(self, book: str) -> None:
        self._book_num = None
        if book is None:
            self._book = None

        else:
            book = re.sub(r'\s+', ' ', book).strip()
            if book_to_number(book) is None:
                raise BookNameNotFound(book_name=book)
            self._book = book

    def book_num(self) -> int | None:
        if self.book() is None:
            return None
        return book_to_number(self.book())

    def set_book_num(self, num: int):
        self._book_num = num

    def chapter(self) -> str:
        return self._chapter

    def set_chapter(self, chapter) -> None:
        if chapter:
            chapter = re.sub(r'\s', '', chapter)
            chapter = re.sub(r'–', '-', chapter)

        self._chapter = chapter

    def verse(self) -> str:
        return self._verse

    def verse_int(self) -> int:
        return int(self.verse())

    def verse_list(self) -> list:
        if self.verse():
            return re.split(r'\s*[,،]\s*', self.verse())

        return []

    def verse_formatted(self, lang: Language = EnglishLanguage) -> str:
        if self.verse():
            verses = []
            for v in self.verse_list():
                match = re.match(r'^\s*(?P<start>\d+)\s*(-)\s*(?P<end>\d+)\s*$', v)
                if match:
                    verses += [num for num in range(int(match.group('start')), int(match.group('end')) + 1)]
                else:
                    verses.append(int(v))

            last: int = None
            start: int = None
            text = ''
            verses.sort()
            for v in verses:
                if last is None:
                    start = v

                elif v != last + 1:
                    if start != last:
                        text += ('' if not text else lang.verse_delim()) + f'{start}-{last}'
                    else:
                        text += ('' if not text else lang.verse_delim()) + str(last)

                    start = v

                last = v

            if not start == last:
                text += ('' if not text else lang.verse_delim()) + f'{start}-{last}'
            else:
                text += ('' if not text else lang.verse_delim()) + str(last)

            return text

        return ''

    def set_verse(self, verse) -> None:
        if verse:
            verse = re.sub(r'\s{2,}', ' ', verse.strip())
            verse = re.sub(r'–', '-', verse)

        self._verse = verse

    # @deprecated("Use is_valid() instead.")
    def is_ref_valid(self) -> bool:
        return self.is_valid()

    def is_valid(self) -> bool:
        if not self._ref_valid:
            return False

        if self.ref_type == ResultType.BOOK_VERSE:
            return bool(self.book_num() and self.verse())

        elif self.ref_type == ResultType.BOOK_CHAPTER:
            return bool(self.book_num() and self.chapter())

        return bool(self.book_num() and self.chapter() and self.verse())

    def set_ref_text(self, ref: str) -> None:
        self._set_ref_text = ref

    def text(self,
             language: Language = EnglishLanguage(),
             mime_type: str = 'latex',
             style: VerseStyle = VerseStyle.STANDARD,
             rtl_spacer: str = None) -> str:
        ref = ''

        if self.text_before:
            ref += self.text_before

        if not self.book_hidden and not self.chapter_hidden:
            book: str | None = None

            if style == VerseStyle.TEXT:
                book = self.text_book

            elif self.book_num():
                book = proper_books_names(self.book_num(), lang_code=language.code(), style=style)

            elif self.book():
                log_warning(
                    f'Book name "{self.book()}" is not defined for lang: {language.code()},' \
                    f' chapter: {self.chapter()}, verse: {self.verse()}'
                )

                book = self.book()

            if book:
                if self.book_prefix:
                    book = self.book_prefix + book

                if mime_type == 'latex':
                    book = book.replace(' ', '\\,')

                ref += (' ' if ref else '') + book

        if not self.chapter_hidden and self.chapter():
            if ref:
                ref += '\\,' if mime_type == 'latex' else ' '
            ref += self.chapter()

        if self.verse():
            if not self.chapter_hidden and self.chapter():
                ref += ':'
                if language.direction() == DIRECTIONS.RTL and rtl_spacer:
                    ref += rtl_spacer
                    # ref += '\u200f'

            ref += self.verse()

        if self.text_after:
            ref += self.text_after

        if language.script() == ArabicScript:
            return arabic2indic(ref)

        return ref

    def text_ar(self, style: VerseStyle = VerseStyle.TEXT, rtl_spacer: str = '\u200f', mime_type: str = 'latex') -> str:
        return self.text(
            language=ArabicLanguage(),
            mime_type=mime_type,
            style=style,
            rtl_spacer=rtl_spacer,
        )


class VerseReferenceList(list):
    # verse_refs: list[VerseReference] = []

    text_before: str = ''
    text_after: str = ''
    in_index: bool = True
    page: int

    def __init__(self, *args, text: str = None, page: int = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.page = page
        if text:
            self.parse_text(text)

    def parse_text(self, text: str):
        if m := re.search(r'^(?P<mod>\s*[!*]\s*)(?P<ref>.*)$', text):
            self.in_index = False
            text = m['ref']

        refs = self._parse_text(text)
        i = 0
        while i < len(refs):
            if isinstance(refs[i], str):
                if i == 0:
                    self.text_before = refs[i]
                elif i == len(refs) - 1:
                    self.text_after = refs[i]
                else:
                    refs[i-1].text_after += refs[i]
                del refs[i]
            else:
                i += 1

        last_book = None
        last_chapter = None
        for r in refs:
            if r.book():
                last_book = r.book()
            elif last_book:
                print('Setting book:', last_book, file=sys.stderr)
                r.set_book(last_book)
                r.book_hidden = True
            else:
                print('No book!', r.text(), file=sys.stderr)

            if r.chapter():
                last_chapter = r.chapter()
            elif last_chapter:
                r.set_chapter(last_chapter)
                r.chapter_hidden = True

            if r.book_num() is None and r.book():
                print('book_num = None', re.sub(r'\s+', ' ', r.text_ar()), file=sys.stderr)

        for x in refs:
            self.append(x)

    def _parse_text(self, text: str) -> list:
        result = parse_verse_reference(text, page=self.page)
        if result.found:
            vr = result.verse_factory()
            if isinstance(vr, VerseReference):
                vr.text_before = ''
                vr.text_after = ''
            return self._parse_text(result.text_before) + [vr] + self._parse_text(result.text_after)
        return [text]

    def valid(self) -> bool:
        return self.empty() or len([vr for vr in self if vr.is_valid()]) == len(self)

    def empty(self) -> bool:
        return len(self) > 0

    def append(self, child) -> None:
        if isinstance(child, VerseReference):
            child.parent = self
            child.order0 = len(self)
        # log_debug('order0: %s' % vr.order0)
        super().append(child)

    def text(self,
             language: Language = EnglishLanguage(),
             mime_type: str = 'latex',
             style: VerseStyle = VerseStyle.STANDARD,
             rtl_spacer: str = None) -> str:

        ref = self.text_before if self.text_before else ''
        for vr in self:
            ref += vr.text_before if vr.text_before else ''
            ref += vr.text(language=language, style=style, rtl_spacer=rtl_spacer, mime_type=mime_type)
            ref += vr.text_after if vr.text_after else ''

        ref += self.text_after if self.text_after else ''

        return ref


class VerseReferenceRange(VerseReferenceAbstract):
    _begin: VerseReference | None
    _end: VerseReference | None

    def __init__(self, begin: VerseReference = None, end: VerseReference = None):
        self.set_begin(begin)
        self.set_end(end)

    def begin(self):
        return self._begin

    def set_begin(self, vr: VerseReference):
        self._begin = vr

    def end(self):
        return self._end

    def set_end(self, vr: VerseReference):
        self._end = vr

    def verse_formatted(self, lang: Language = EnglishLanguage) -> str:
        pass

    def text(self, language: Language = EnglishLanguage, mime_type: str = 'html', style: str = None) -> str:
        pass


class Marker:
    text_before: str | None = None
    text_after: str | None = None

    def __init__(self, symbol: str):
        self._symbol = None

        self.set_symbol(symbol)

    def symbol(self) -> str:
        return self._symbol

    def set_symbol(self, symbol: str) -> None:
        self._symbol = symbol


@unique
class ResultType(Flag):
    BOOK_CHAPTER_VERSE = 1
    BOOK_CHAPTER = 2
    BOOK_VERSE = 4
    CHAPTER_VERSE = 8
    VERSE = 16
    MARKER = 32
    UNKNOWN = 64
    BOOK = 128
    DELIMITER = 256
    ANY_REF = BOOK | BOOK_CHAPTER_VERSE | BOOK_CHAPTER | BOOK_VERSE | CHAPTER_VERSE | VERSE | DELIMITER


@dataclass
class ParseResult:

    found: bool = False
    object: VerseReference = None
    text: str | None = None
    text_book: str | None = None
    text_before: str | None = ''
    text_after: str | None = ''
    type: ResultType | None = None
    prefix: str | None = ''

    auths: list[str] = field(default_factory=list)
    book: str | None = None
    book_num: int | None = None
    book_hidden: bool = False
    chapter: str | None = None
    chapter_hidden: bool = False
    verse: str | None = None
    token: str | None = None

    def __repr__(self) -> str:
        return f"ParseResult<found: {self.found}, text_before: '{self.text_before}'," \
            f" text_after, '{self.text_after}', type: {self.type}>"

    def __str__(self) -> str:
        return self.render()

    def render(self, verse_style: VerseStyle = VerseStyle.STANDARD) -> str:
        text = ''
        if self.book:
            text += (' ' if text else '') + (self.book if verse_style != VerseStyle.TEXT else self.text_book)

        if self.chapter:
            text += (' ' if text else '') + self.chapter

        if self.verse:
            text += (':' if self.chapter else '') + (' ' if text else '') + self.verse

        return text

    def verse_factory(self) -> VerseReference | None:
        if self.type == ResultType.MARKER:
            ref = Marker(symbol=self.token)

        elif self.type == ResultType.DELIMITER:
            return self.token

        elif self.type:
            # print(f'ParseResult: {self}', file=sys.stderr)
            ref = VerseReference(
                book=self.book,
                book_prefix=self.prefix,
                book_num=self.book_num,
                chapter=self.chapter,
                verse=self.verse,
                authorities=self.auths
            )
            ref._set_ref_text = self.text
            ref.text_book = self.text_book if self.text_book is not None else ''
            ref.book_hidden = self.book_hidden
            ref.chapter_hidden = self.chapter_hidden
            ref.ref_type = self.type
            ref._ref_valid = self.found  # pylint: disable=protected-access

        else:
            return None

        ref.text_before = self.text_before
        ref.text_after = self.text_after

        return ref


@dataclass
class NameResult:
    found: bool = False
    prefix: str = ''
    name: str = None
    num: int = None


def check_book_name(name: str) -> NameResult | None:
    if num := book_to_number(ArabicScript.strip_text(indic2arabic(name))):
        return NameResult(found=True, name=name, num=num)

    # U0650 is kesra
    if (m := re.search(r'^(?P<prefix>[وبل]\u0650*)(?P<name>.*)$', name)) \
            and (num := book_to_number(ArabicScript.strip_text(indic2arabic(m.group('name'))))):
        return NameResult(found=True, prefix=m.group('prefix'), name=m.group('name'), num=num)

    return None


def parse_verse_reference(text: str, page: int = None, result_type: ResultType = ResultType.ANY_REF) -> ParseResult:
    res = [
        {
            'type': ResultType.DELIMITER,
            're': re.compile(
                r"""
                    ^
                    (?P<delimiter>[;,،؛]\s*)
                    (?P<after>.*?)
                    $
                """,
                re.VERBOSE | re.UNICODE
            )
        },
        {
            'type': ResultType.BOOK_CHAPTER_VERSE,
            're': re.compile(
                r"""
                    (?P<before>^|\W)
                    (?P<book>
                        (
                            [123A-Z][a-z]+
                            |
                            [١٢٣123]\s*[{chars}]+\s*[{chars}]+
                            |
                            [{chars}]+\s*[{chars}]*\s*[{chars}]+
                        )
                    )
                    (?P<hidebook>[!*]*)
                    (\.|\s+)
                    (?P<chapter>\d([\d\s,،\-–]*\d|))
                    (?P<hidechapter>[!*]*)
                    (\.|\s*:\s*)
                    (?P<verse>\d([\d\s,،\-–]*\d|))
                    (?P<after>\D|$)
                """.format(chars=ArabicScript.re_char_class()),
                re.VERBOSE | re.UNICODE
            )
        },
        {
            'type': ResultType.BOOK_CHAPTER,
            're': re.compile(
                r"""
                    (?P<before>^|\W)
                    (?P<book>
                        (
                            [123A-Z][a-z]+
                            |
                            [١٢٣123]\s*[{chars}]+\s*[{chars}]+
                            |
                            [{chars}]+\s*[{chars}]*\s*[{chars}]+
                        )
                    )
                    (\.|\s*)
                    (?P<hidebook>[!*]*)
                    (?P<chapter>\d([\d\s,،\-–]*\d|))
                    (?P<after>\D|$)
                """.format(chars=ArabicScript.re_char_class()),
                re.VERBOSE | re.UNICODE
            )
        },
        {
            'type': ResultType.CHAPTER_VERSE,
            're': re.compile(
                r"""
                    (?P<before>^|\W)
                    (?P<chapter>\d([\d\s,،\-–]*\d|))
                    (?P<hidechapter>[!*]*)
                    (\.|\s*:\s*)
                    (?P<verse>\d([\d\s,،\-–]*\d|))
                    (?P<after>\D|$)
                """,
                re.VERBOSE | re.UNICODE
            )
        },
        {
            'type': ResultType.VERSE,
            're': re.compile(
                r"""
                    (?P<before>^|[\Wو])
                    (?P<verse>\d([\d\s,،\-–]*\d|))
                    (?P<after>\D|$)
                """,
                re.VERBOSE | re.UNICODE
            )
        },
        # {
        #     'type': ResultType.VERSE,
        #     're': re.compile(r'(?P<before>\s*)(|(?P<auths>[A-Z,]+):)(?P<verse>\d+)(?P<after>\D+|$)')
        # },
        {
            'type': ResultType.MARKER,
            're': re.compile(r'(?P<before>^|\W)(?P<token>[פס])(?P<after>\W|$)', re.UNICODE)
        },
    ]

    # log_debug('parsing text: "%s"' % text)

    result = ParseResult()

    text = text.replace('\u200f', '')
    text = indic2arabic(text)

    #if '3 يوح' in text:
    #    raise Exception(':'.join([hex(ord(c)) for c in text]), page)

    vr = None
    match = False
    cb_type = None
    for row in [r for r in res if r['type'] in result_type]:
        match = row['re'].search(text)
        if match:
            cb_type = row['type']

            start = match.end('before') if 'before' in match.groupdict() else 0
            end = match.start('after')
            result.book_hidden = bool('hidebook' in match.groupdict() and match['hidebook'])
            result.chapter_hidden = bool('hidechapter' in match.groupdict() and match['hidechapter'])

            result.text = text[start:end]
            result.text_before = text[:start]
            result.text_after = text[end:]
            break

    terms_list = [
        r'قارن',
        r'انظر\s+ايضا',
        r'انظر\s+كذلك',
        r'انظر',
        r'راجع',
        r'cf\.',
        r'cf',
        r'see',
        r'see\s+also',
        r'&',
        r'and',
        r'و'
    ]

    terms = '|'.join(terms_list)
    re_terms = re.compile(fr'^\s*(?P<term>({terms}))\s*', re.IGNORECASE | re.UNICODE)

    # if cb_type and 'auths' in match.groupdict() and match['auths']:
    #     result.auths = re.split(r',', match['auths'])
    if cb_type in [ResultType.BOOK_CHAPTER_VERSE, ResultType.BOOK_CHAPTER]:
        result.text_book = match['book']
        if m := re_terms.search(ArabicScript.strip_text(result.text_book)):
            result.text_before += m['term']
            result.text_book = re_terms.sub('', ArabicScript.strip_text(result.text_book))
            result.text = re_terms.sub('', ArabicScript.strip_text(result.text))

        elif ArabicScript.strip_text(result.text_book) in terms_list:
            result.text_before += result.text_book
            result.text_book = None

        if not result.text_book:
            if cb_type == ResultType.BOOK_CHAPTER_VERSE:
                cb_type = ResultType.CHAPTER_VERSE
            elif cb_type == ResultType.BOOK_CHAPTER:
                cb_type = ResultType.UNKNOWN
                result.found = False

        else:
            result.book = result.text_book
            if r := check_book_name(result.book):
                result.prefix = r.prefix
                result.book = r.name
                result.book_num = r.num
                result.found = True

            else:
                words = re.split(r'\s+', result.book)
                if len(words) == 3 and (r := check_book_name(' '.join(words[1:]))):
                    result.text_before += (' ' if result.text_before and result.text_before[-1] != ' ' else '') + words[0] + ' '
                    result.text = re.sub(fr'^{words[0]}\s+', '', result.text)
                    result.prefix = r.prefix
                    result.book = r.name
                    result.book_num = r.num
                    result.text_book = ' '.join(words[1:])
                    result.found = True

                elif len(words) > 1 and (r := check_book_name(words[-1])):
                    result.text_before += (' ' if result.text_before and result.text_before[-1] != ' ' else '') + ' '.join(words[:-1]) + ' '
                    result.text = re.sub(fr'^{words[0]}\s+{words[1]}\s+', '', result.text)
                    result.prefix = r.prefix
                    result.book = r.name
                    result.book_num = r.num
                    result.text_book = words[-1]
                    result.found = True

                else:
                    result.found = False
                    raise BookNameNotFound(result.book, text, page=page)

    if cb_type in [ResultType.BOOK_CHAPTER_VERSE, ResultType.BOOK_CHAPTER, ResultType.CHAPTER_VERSE]:
        result.chapter = indic2arabic(match['chapter'])
        result.found = True

    if cb_type in [ResultType.BOOK_CHAPTER_VERSE, ResultType.CHAPTER_VERSE, ResultType.VERSE]:
        result.verse = indic2arabic(match['verse'])
        result.found = True

    if result.found:
        # log_debug('%s %s : %s' % (result.book, result.chapter, result.verse))
        result.type = cb_type

    elif cb_type == ResultType.MARKER:
        result.type = cb_type
        result.token = match.group('token')
        result.found = True

    elif cb_type == ResultType.DELIMITER:
        result.type = cb_type
        result.token = match['delimiter']
        result.found = True

    if match and result.found:
        # result.found = True
        vr = result.verse_factory()
        if cb_type in [ResultType.BOOK_CHAPTER_VERSE, ResultType.BOOK_CHAPTER] \
                and vr.book() \
                and book_to_number(vr.book()) \
                and book_to_number(vr.book()) in BibleBooks.single_chapter_books():
            if vr.verse() and vr.chapter():
                log_warning(f'Verse ref has a chapter but it should not {vr.book()} {vr.chapter()} : {vr.verse()}')
            else:
                vr.set_verse(vr.chapter())
                vr.set_chapter(None)
                vr.ref_type = ResultType.BOOK_VERSE
                result.type = ResultType.BOOK_VERSE

        # log_debug('[%s]' % match.group('book'))
        # log_debug(str(result))

    return result


# noinspection PyShadowingNames


class _MatchResult:
    def __init__(self):
        super().__init__()

        self.found = False
        self.end = 0
        self.text_before: str | None = None
        self.text_after: str | None = None
        self.book: str | None = None
        self.auths = []
        self.chapter: str | None = None
        self.verse: str | None = None
        self.digit: str | None = None

    def kind(self):
        if self.found:
            if self.book:
                if self.chapter:
                    if self.verse:
                        return ResultType.BOOK_CHAPTER_VERSE
                    else:
                        return ResultType.BOOK_CHAPTER
                elif self.verse:
                    return ResultType.BOOK_VERSE
                else:
                    return ResultType.BOOK

            elif self.chapter and self.verse:
                return ResultType.CHAPTER_VERSE

            elif self.digit:
                return ResultType.VERSE

        return ResultType.UNKNOWN

    def verse_reference_object(self):
        return VerseReference(book=self.book, chapter=self.chapter, verse=self.verse, authorities=self.auths)


# noinspection PyShadowingNames
def _match_single_reference(text: str, lang: Language = EnglishLanguage) -> _MatchResult:
    match = _match_book(text)  # type: _MatchResult

    result = _MatchResult()

    if match.found:
        result.book = match.book
        result.auths = match.auths
        result.text_after = match.text_after

        text = match.text_after

    match = _match_colon(text)

    if match.found:
        result.chapter = match.chapter
        result.verse = match.verse
        result.text_after = match.text_after

    else:
        match = _match_digit(text)

        if match.found:
            result.chapter = match.digit
            result.text_after = match.text_after

    return result


_re_book = re.compile(r"""
            (
                |
                (?P<auths>[A-Z,]+):
            )
            (?P<book>
                (
                    [123A-Z][a-z]+
                    |
                    [١٢٣123]\s*[{chars}]+\s*[{chars}]+
                    |
                    [{chars}]+\s*[{chars}]*\s*[{chars}]+
                )
            )
        """.format(chars=ArabicScript.re_char_class()), re.VERBOSE)


def _match_book(text: str) -> _MatchResult:

    result = _MatchResult()
    result.book = None
    result.auths = []

    match = _re_book.match(text)
    if match:
        result.found = True
        result.end = match.end(0)
        result.book = match.group('book')
        result.text_after = text[match.end(0):]
        result.text_before = text[:match.start(0)]

        if match.group('auths'):
            result.auths = re.split(r'\s*,\s*', match.group('auths'))

    return result


_re_colon = re.compile(r'(?P<chapter>\d+)(?P<colon>\s*[:.]\s*)(?P<verse>\d+)')


# noinspection PyShadowingNames
def _match_colon(text: str, lang: Language = EnglishLanguage) -> _MatchResult:

    result = _MatchResult()
    result.chapter = None
    result.verse = None

    match = _re_colon.match(text)
    if match:
        colon = match.group('colon')
        result.found = True
        result.end = match.end(0)
        result.text_after = text[match.end(0):]
        result.text_before = text[:match.start(0)]

        if lang.name() == LANGUAGES.ARABIC and ' ' not in colon and '\u0200' not in colon:
            result.chapter = match.group('verse')
            result.verse = match.group('chapter')
        else:
            result.chapter = match.group('chapter')
            result.verse = match.group('verse')

    return result


def _match_re(regexp: re.Pattern, text: str) -> _MatchResult:

    result = _MatchResult()

    match = regexp.match(text)
    if match:
        result.found = True
        result.end = match.end()
        result.text_after = text[match.end(0):]
        result.text_before = text[:match.start(0)]

        result.dash = match.group(0)

    return result


_re_digit = re.compile(r'\d+')
_re_dash = re.compile(r'[\s\u0200]*-[\s\u0200]*')
_re_comma = re.compile(r'[\s\u0200]*[,،][\s\u0200]*')


def _match_digit(text: str) -> _MatchResult:
    return _match_re(_re_digit, text)


def _match_dash(text: str) -> _MatchResult:
    return _match_re(_re_dash, text)


def _match_comma(text: str) -> _MatchResult:
    return _match_re(_re_comma, text)


@dataclass
class ReferenceTextBlock:
    text: str

    def __str__(self):
        return self.text

    def print(self):
        print(f'TXT: "{self.text}"')


@dataclass
class ReferencePartBlock(ReferenceTextBlock):
    type: ResultType

    def __repr__(self):
        return f"'{self.text}' #{self.type.value}"


@dataclass
class ReferenceBlock:
    parts: list[ReferencePartBlock] = field(default_factory=list)

    def __str__(self):
        suffix = ''
        text = self.text
        if self.parts and self.parts[-1].type == ResultType.DELIMITER:
            suffix = self.parts[-1].text
            text = ''.join([part.text for part in self.parts[:-1]])

        if m := re.search(r'(?P<spaces>\s+)$', text):
            suffix += m['spaces']

        return f'<< {text.strip()} >>{suffix}'

    def print(self):
        print('REF:', self.text, self.parts)

    def add_part(self, part: ReferencePartBlock):
        self.parts.append(part)

    def is_verse(self) -> bool:
        return len(self.parts) == 1 and self.parts[0].type == ResultType.VERSE

    @property
    def text(self):
        return ''.join([part.text for part in self.parts])


def parse_spans(text: str, page: int = None):
    results = None
    try:
        results = parse_verse_reference(text, page=page)
        # print('Before: "%s"' % results.text_before)
    except BookNameNotFound as exc:
        m = re.match(r'((.{1,10}|^.*?)%s(.{1,10}|.*?$))' % exc.book_name, text)
        print(f'{exc.book_name} -- {m[1] if m else ""}  Page: {page}')

    if not results or not results.found:
        return [ReferenceTextBlock(text=text)]

    return parse_spans(results.text_before, page=page) + [ReferencePartBlock(text=results.text, type=results.type)] + parse_spans(results.text_after, page=page)


def tokenize_text(text: str, page: int = None):
    spans: list[ReferenceTextBlock | ReferenceBlock] = []

    for span in parse_spans(text, page=page):
        if isinstance(span, ReferencePartBlock):
            if not spans or not isinstance(spans[-1], ReferenceBlock):
                spans.append(ReferenceBlock())
            spans[-1].add_part(span)

        elif isinstance(span, ReferenceTextBlock):
            if span.text:
                spans.append(span)

    i = 0
    while i < len(spans):
        if isinstance(spans[i], ReferenceBlock) and spans[i].is_verse():
            spans[i] = ReferenceTextBlock(text=spans[i].text)

        if i > 0 and isinstance(spans[i], ReferenceTextBlock) and isinstance(spans[i - 1], ReferenceTextBlock):
            spans[i - 1].text += spans[i].text
            del spans[i]
        else:
            i += 1

    return spans
