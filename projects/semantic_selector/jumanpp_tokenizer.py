# -*- coding: utf-8 -*-
import re
import os
import unicodedata
import mysql.connector
import mojimoji

from pyknp import Jumanpp
from bs4 import BeautifulSoup
from mstranslator import Translator
from urllib.parse import urlparse


class InputTagTokenizer(object):
    class __InputTagTokenizer(object):
        def __init__(self):
            self.tokenizer = Jumanpp()
            self.translator = Translator(os.environ['TRANSLATOR_TEXT_API_KEY'])
            self.target_attributes = [
                'name',
                'type',
                'id',
                'value',
                'alt',
                'placeholder'
            ]
            self.exclude_words = [
                "",
                ".",
                "(",
                ")",
                "/",
                "\n",
                "\t"
            ]

            url = urlparse('mysql://root@localhost:3306/translator')
            self.connection = mysql.connector.connect(
                host=url.hostname or 'localhost',
                port=url.port or 3306,
                user=url.username or 'root',
                password=url.password or '',
                database=url.path[1:],
            )

        def jumanpp_tokenize(self, text):
            ret = []
            if not text.rstrip():
                return ret

            try:
                result = self.tokenizer.analysis(text)
                for mrph in result.mrph_list():
                    if mrph.hinsi in ['名詞', '動詞', '形容詞'] or mrph.imis in ['品詞推定:名詞']:
                        word = mrph.midasi
                        if word in self.exclude_words:
                            continue
                        if self.__is_japanese(word):
                            word = self.__translate(word)
                        ret.append(word)

            except IndexError:
                print("[WARN] That was no valid value :" + text)

            return ret

        def get_attrs_value(self, html):
            html_soup = BeautifulSoup(html, 'html.parser')

            s = html_soup.find('input')
            if s is not None:
                return self.__attrs_values_from_input(s)

            s = html_soup.find('select')
            if s is not None:
                return self.__attrs_values_from_select(s)

            return []

        def __attrs_values_from_input(self, input_tag):
            words = []
            for k in self.target_attributes:
                if (k not in input_tag.attrs) or (input_tag.attrs[k] == ''):
                    continue

                for token in self.__preprocess(input_tag.attrs[k]):
                    words.append(token)

            return words

        def __attrs_values_from_select(self, select_tag):
            words = []
            for k in self.target_attributes:
                if (k not in select_tag.attrs) or (select_tag.attrs[k] == ''):
                    continue

                for token in self.__preprocess(select_tag.attrs[k]):
                    words.append(token)

            inner_options = select_tag.find_all('option')
            for option in inner_options:
                if len(option.contents) > 0:
                    word = option.contents[0]
                    for token in self.__preprocess(word):
                        words.append(token)

            return words

        def __convert_to_snake(self, name):
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        def __to_word(self, word):
            if re.match(r'[^@]+@[^@]+\.[^@]+', word):
                return 'e-mail'
            return word

        def __preprocess(self, value):
            value = self.__to_word(value)
            snake_case_value = self.__convert_to_snake(value)
            snake_case_value = re.sub(r'([0-9]+)', r'_\1', snake_case_value)
            tokens = re.split(r'[-_\]\[ ]', snake_case_value)
            for t in tokens:
                t = mojimoji.han_to_zen(t)
                japanese_tokens = self.jumanpp_tokenize(t)
                for j_t in japanese_tokens:
                    if j_t in self.exclude_words:
                        continue
                    yield j_t

        def __translate(self, word):
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM dictionary WHERE japanese = %s', [word])
            translated = cursor.fetchone()
            if translated is not None:
                return translated['english']
            translated = self.translator.translate(text=word, lang_from='ja', lang_to='en')
            try:
                cursor.execute('INSERT INTO dictionary (japanese, english) VALUES (%s, %s)', [word, translated])
                self.connection.commit()
            except:
                self.connection.rollback()
                raise
            return translated

        @staticmethod
        def __is_japanese(text):
            for ch in text:
                name = unicodedata.name(ch)
                if "CJK UNIFIED" in name \
                        or "HIRAGANA" in name \
                        or "KATAKANA" in name:
                    return True
            return False

    instance = None

    def __init__(self):
        if not InputTagTokenizer.instance:
            singleton_instance = InputTagTokenizer.__InputTagTokenizer()
            InputTagTokenizer.instance = singleton_instance

    def __getattr__(self, name):
        return getattr(self.instance, name)


if __name__ == "__main__":
    print("preprocessor")
