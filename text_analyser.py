import re
import difflib
import string

import pymorphy2

from numbers_parser import NumbersParser
from product import Product
from static import State, Intent, INTENT_TO_PHRASES, STOPWORDS, POSITION_TOKENS
from api import send_transaction

MIN_PRODUCT_NAME_THRESHOLD = 0.7
MAX_PRODUCT_NAME_THRESHOLD = 1.1
MIN_DIGITS_IN_CODE = 8


class TextAnalyser:
    def __init__(self, products_list_path, bag_code):
        self.lemmatizer = pymorphy2.MorphAnalyzer()
        self.numbers_parser = NumbersParser()
        self.state = State.BEFORE_START
        self.numbers_regex = re.compile('^[0-9]+$')
        self.bag_code = bag_code

        self.products_list = []
        with open(products_list_path) as fin:
            fin.readline()
            for line in fin:
                line_list = line.strip().split(',')[-3:]
                self.products_list.append(Product(*(line_list + [self.convert_name(line_list[1])])))

    def convert_name(self, name):
        converted_name = []
        tokens = name.lower().split(' ')

        new_tokens = []
        for token in tokens:
            for p in string.punctuation:
                if p == '%':
                    continue
                token = token.replace(p, ' ')
            new_tokens.append(token.strip())

        tokens = [token for token in ' '.join(new_tokens).split(' ') if len(token) > 0]

        for token in tokens:
            if token.endswith('кг') and self.numbers_regex.match(token[: -2]) is not None:
                converted_name.append(token[: -2])
                converted_name.append('килограмм')

            elif token.endswith('г') and self.numbers_regex.match(token[: -1]) is not None:
                converted_name.append(token[: -1])
                converted_name.append('грамм')

            elif token.endswith('мл') and self.numbers_regex.match(token[: -2]) is not None:
                converted_name.append(token[: -2])
                converted_name.append('миллилитр')

            elif token.endswith('л') and self.numbers_regex.match(token[: -1]) is not None:
                converted_name.append(token[: -1])
                converted_name.append('литр')

            elif token.endswith('шт') and self.numbers_regex.match(token[: -2]) is not None:
                converted_name.append(token[: -2])
                converted_name.append('штук')

            elif token.endswith('%'):
                if self.numbers_regex.match(token[: -1]) is not None:
                    converted_name.append(token[: -1])
                    converted_name.append('процент')
                else:
                    converted_name.append(self.lemmatize(token[: -1]))

            else:
                converted_name.append(self.lemmatize(token))

        return ' '.join(converted_name)

    def get_intent(self, tokens):
        text = ' '.join([t for t in tokens if (self.numbers_regex.match(t) is None and t not in STOPWORDS)])

        for intent in [
            Intent.ADD_BAGS,
            Intent.REMOVE_BAGS,
            Intent.REQUEST_WEIGHTING,
            Intent.REQUEST_PAYMENT,
            Intent.ADD_PROMO_CODE,
            Intent.PASS_LOYALTY,
            Intent.GATHER_BONUS,
            Intent.SPEND_BONUS,
            Intent.CANCEL_PAYMENT,
            Intent.CANCEL_ORDER,
            Intent.ADD_PRODUCT,
            Intent.REMOVE_PRODUCT,
            Intent.START,
        ]:
            for phrase in INTENT_TO_PHRASES[intent]:
                if text.startswith(phrase):
                    return intent

        return Intent.NO_MATCH

    @staticmethod
    def get_intersection_length(string_1, string_2):
        return max(difflib.SequenceMatcher(None, string_1, string_2).get_matching_blocks(), key=lambda x: x.size).size

    def get_product_by_name(self, tokens):
        def get_best_intersection_length(product_tokens):
            used_token_indices = set()
            total_intersection_length = 0

            for p_token in product_tokens:
                best_token_index = -1
                best_token_length = 0

                for index, token in enumerate(tokens):
                    if index in used_token_indices:
                        continue

                    length = self.get_intersection_length(p_token, token)
                    if length > best_token_length and length > round(len(p_token) / 2):
                        best_token_index = index
                        best_token_length = length

                if best_token_index > -1:
                    used_token_indices.add(best_token_index)
                    total_intersection_length += best_token_length

            return total_intersection_length

        best_product = None
        best_product_length = -1
        best_score = -1

        for product in self.products_list:
            product_length = len(product.converted_name)
            intersection_length = get_best_intersection_length(product.converted_name.split(' '))

            score = intersection_length / product_length

            if (score > MIN_PRODUCT_NAME_THRESHOLD and
                product_length > best_product_length and
                (best_score < MAX_PRODUCT_NAME_THRESHOLD)):

                best_product_length = product_length
                best_product = product
                best_score = score

        return best_product

    def get_product_by_code(self, code):
        if code is None:
            return None

        for product in self.products_list:
            if product.code == code:
                return product

        return None

    def get_product_position(self, tokens):
        for index, token in enumerate(tokens):
            if token in POSITION_TOKENS:
                if index != len(tokens) - 1:
                    match = self.numbers_regex.match(tokens[index + 1])
                    if match is not None:
                        return int(match.group())
        return None

    def get_code(self, tokens):
        max_num_numbers = 0
        max_index = None
        current_num_numbers = 0

        for index, element in enumerate([int(self.numbers_regex.match(t) is not None) for t in tokens]):
            if element == 1:
                if max_index is None:
                    max_index = index

                current_num_numbers += 1
            else:
                if max_index is None:
                    continue

                if current_num_numbers > max_num_numbers:
                    max_num_numbers = current_num_numbers
                    max_index = index - max_num_numbers

                current_num_numbers = 0

        if current_num_numbers > max_num_numbers:
            max_num_numbers = current_num_numbers
            max_index = index - max_num_numbers + 1

        if max_num_numbers > 0:
            return ''.join(tokens[max_index: (max_index + max_num_numbers)])

        return None

    def lemmatize(self, token):
        return self.lemmatizer.parse(token.strip())[0].normal_form.replace('ё', 'е')

    def parse(self, text):
        try:
            text = text.strip().lower().replace('ё', 'е')

            tokens = [self.lemmatize(t) for t in text.split(' ') if len(t) > 0]
            tokens = self.numbers_parser.parse(tokens)

            intent = self.get_intent(tokens)

            print(f'DEBUG: source text: {text}')
            print(f'DEBUG: tokens:      {tokens}')
            print(f'DEBUG: intent:      {intent}')
            print(f'DEBUG: state:       {self.state}\n')

            if intent == Intent.START:
                if self.state == State.BEFORE_START:
                    self.state = State.AFTER_START
                    return {'message:': 'Начинаем обрабатывать новый заказ'}
                else:
                    return {'message': 'Заказ уже обрабатывается'}

            if intent == Intent.NO_MATCH:
                # we don't want to change state here
                return {'message': 'Не удалось распознать фразу'}

            # in all cases get only first best match, ignore others
            code = self.get_code(tokens)
            amount = None

            if code is not None:
                amount = int(code)
                if len(code) < MIN_DIGITS_IN_CODE:
                    code = None

            product_by_name = self.get_product_by_name(tokens)
            product_by_code = self.get_product_by_code(code)
            product_position = self.get_product_position(tokens)

            return self.process_result(intent, code, amount, product_by_name, product_by_code, product_position,
                                       product_by_name is None, product_by_code is None, product_position is None)
        except Exception as e:
            print(f'DEBUG: Error:{e}')

        return {'message': 'Ошибка сервиса'}

    def process_result(self, intent, code, amount, product_by_name,
                       product_by_code, product_position, no_n, no_c, no_p):

        if intent == Intent.ADD_PRODUCT or intent == Intent.REQUEST_WEIGHTING:
            if self.state == State.WHILE_PAYMENT:
                return {'message': 'Вы уже начали оплату, завершите её или отмените весь заказ'}

            self.state = State.AFTER_START

            if no_n and no_c:
                return {'message': 'Название/штрих-код указан неверно или отсутствует'}

            if no_n and not no_c:
                send_transaction(intent, code=product_by_code.code)
                return {'message': 'Успешно', 'product': product_by_code}

            if not no_n and no_c:
                send_transaction(intent, code=product_by_name.code)
                return {'message': 'Успешно', 'product': product_by_name}

            if product_by_name.code == product_by_code.code:
                send_transaction(intent, code=product_by_name.code)
                return {'message': 'Успешно', 'product': product_by_name}

            return {'message': 'Указано больше одного продукта'}

        if intent == Intent.REMOVE_PRODUCT:
            if self.state == State.WHILE_PAYMENT:
                return {'message': 'Вы уже начали оплату, завершите её или отмените весь заказ'}

            self.state = State.AFTER_START

            if no_n and no_c and no_p:
                return {'message': 'Название/штрих-код/позиция указан(-а) неверно или отсутствует'}

            if not no_p:
                if not no_n or not no_c:
                    return {'message': 'Укажите или название, или штрих-код, или позицию'}
                else:
                    send_transaction(intent, position=product_position)
                    return {'message': 'Успешно', 'position': product_position}

            if no_n and not no_c:
                send_transaction(intent, code=product_by_code.code)
                return {'message': 'Успешно', 'product': product_by_code}

            if not no_n and no_c:
                send_transaction(intent, code=product_by_name.code)
                return {'message': 'Успешно', 'product': product_by_name}

            if product_by_name.code == product_by_code.code:
                send_transaction(intent, code=product_by_name.code)
                return {'message': 'Успешно', 'product': product_by_name}

            return {'message': 'Указано больше одного продукта'}

        if intent == Intent.ADD_BAGS or intent == Intent.REMOVE_BAGS:
            if self.state == State.WHILE_PAYMENT:
                return {'message': 'Вы уже начали оплату, завершите её или отмените весь заказ'}

            self.state = State.AFTER_START

            if no_n and no_c and no_p:
                send_transaction(intent, code=self.bag_code)
                return {'message': 'Успешно', 'product': 'bag'}
            else:
                return {'message': 'Операция с пакетом несовместима с другими операциями'}

        if intent == Intent.REQUEST_PAYMENT:
            if self.state == State.WHILE_PAYMENT or self.state == State.WHILE_LOYALTY_ACTION:
                if no_n and no_c and no_p:
                    send_transaction(intent, final=True)
                    self.state = State.AFTER_START
                    return {'message': 'Успешно', 'action': 'finish-payment'}
                return {'message': 'Оплата заказа несовместима с другими операциями'}

            if no_n and no_c and no_p:
                send_transaction(intent)
                self.state = State.WHILE_PAYMENT
                return {'message': 'Успешно', 'action': 'start-payment'}
            else:
                self.state = State.AFTER_START
                return {'message': 'Оплата заказа несовместима с другими операциями'}

        if intent == Intent.ADD_PROMO_CODE:
            if self.state == State.WHILE_PAYMENT or self.state == State.WHILE_LOYALTY_ACTION:
                self.state = State.WHILE_PAYMENT

                if no_n and no_c and no_p:
                    if code is not None:
                        send_transaction(intent, code=code)
                        return {'message': 'Успешно', 'promo-code': code}
                    else:
                        return {'message': 'Для использования купона необходимо указать корректный код'}
                else:
                    return {'message': 'Использование промо-кода несовместимо с другими операциями'}
            else:
                return {'message': 'Использование промо-кода возможно только в процессе оплаты'}

        if intent == Intent.PASS_LOYALTY:
            if self.state == State.WHILE_PAYMENT or self.state == State.WHILE_LOYALTY_ACTION:
                if no_n and no_c and no_p:
                    if code is not None:
                        self.state = State.WHILE_LOYALTY_ACTION
                        send_transaction(intent, code=code)
                        return {'message': 'Успешно, укажите, накопим баллы или спишем?', 'card-code': code}
                    else:
                        return {'message': 'Для использования карты магазина необходимо корректно указать её номер'}
                else:
                    return {'message': 'Указание карты несовместимо с другими операциями'}
            else:
                return {'message': 'Указание карты магазина возможно только в процессе оплаты'}

        if intent == Intent.GATHER_BONUS or intent == Intent.SPEND_BONUS:
            if self.state != State.WHILE_LOYALTY_ACTION:
                return {'message': 'Сперва надо сказать, что Вы хотите использовать карту магазина и указать её номер'}

            self.state = State.WHILE_PAYMENT

            if no_n and no_c and no_p and code is None:
                if intent == Intent.GATHER_BONUS:
                    return {'message': 'Успешно, баллы накоплены'}
                else:
                    if amount is not None:
                        send_transaction(intent, amount=amount)
                        return {'message': 'Успешно, баллы списаны'}
                    else:
                        return {'message': 'Для списания баллов нужно указать их количество'}
            else:
                return {'message': 'Работа с баллами несовместима с другими операциями'}

        if intent == Intent.CANCEL_PAYMENT:
            if self.state == State.WHILE_PAYMENT or self.state == State.WHILE_LOYALTY_ACTION:
                if no_n and no_c and no_p:
                    send_transaction(intent)
                    self.state = State.AFTER_START
                    return {'message': 'Успешно', 'action': 'cancel-payment'}
                return {'message': 'Возвращение к выбору товаров для заказа несовместимо с другими операциями'}
            else:
                self.state = State.AFTER_START
                return {'message': 'Прежде чем отменить режим оплаты, вы должны в него перейти'}

        if intent == Intent.CANCEL_ORDER:
            self.state = State.AFTER_START
            send_transaction(intent)
            return {'message': 'Успешно', 'action': 'cancel-order'}
