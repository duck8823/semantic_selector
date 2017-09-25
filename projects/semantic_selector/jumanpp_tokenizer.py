# -*- coding: utf-8 -*-
import re
from pyknp import Jumanpp
from bs4 import BeautifulSoup


class JumanppInputTagTokenizer(object):
    class __JumanppInputTagTokenizer(object):
        def __init__(self):
            self.tokenizer = Jumanpp()
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
                "\n"
            ]

        def jumanpp_tokenize(self, text):
            ret = []
            if not text.rstrip():
                return ret

            try:
                result = self.tokenizer.analysis(text)
                for mrph in result.mrph_list():
                    if mrph.hinsi == '名詞' or mrph.imis == '品詞推定:名詞':
                        ret.append(mrph.midasi)

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

        def __preprocess(self, value):
            snake_case_value = self.__convert_to_snake(value)
            snake_case_value = re.sub(r'([0-9]+)', r'_\1', snake_case_value)
            tokens = re.split(r'[-_\]\[ ]', snake_case_value)
            for t in tokens:
                japanese_tokens = self.jumanpp_tokenize(t)
                for j_t in japanese_tokens:
                    if j_t in self.exclude_words:
                        continue
                    yield j_t

    instance = None

    def __init__(self):
        if not JumanppInputTagTokenizer.instance:
            singleton_instance = JumanppInputTagTokenizer.__JumanppInputTagTokenizer()
            JumanppInputTagTokenizer.instance = singleton_instance

    def __getattr__(self, name):
        return getattr(self.instance, name)


if __name__ == "__main__":
    print("preprocessor")
