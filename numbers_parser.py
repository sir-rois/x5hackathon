WORD_TO_NUMBERS_ZERO = {'ноль': 0, 'нуль': 0}

WORD_TO_NUMBERS_1_9 = {
    'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9,
}

WORD_TO_NUMBERS_10_19 = {
    'десять': 10, 'одиннадцать': 11, 'одинадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14,
    'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18, 'девятнадцать': 19,
}

WORD_TO_NUMBERS_20_90 = {
    'двадцать': 20, 'тридцать': 30, 'сорок': 40, 'пятьдесят': 50,
    'шестьдесят': 60, 'семьдесят': 70, 'восемьдесят': 80, 'девяносто': 90,
}

WORD_TO_NUMBERS_100_900 = {
    'сто': 100, 'двести': 200, 'триста': 300, 'четыреста': 400, 'пятьсот': 500,
    'шестьсот': 600, 'семьсот': 700, 'восемьсот': 800, 'девятьсот': 900,
}

NUMBER_WORDS = set(WORD_TO_NUMBERS_ZERO).union(set(WORD_TO_NUMBERS_1_9)).union(
    set(WORD_TO_NUMBERS_10_19)).union(set(WORD_TO_NUMBERS_20_90)).union(set(WORD_TO_NUMBERS_100_900))


class NumbersParser:
    @staticmethod
    def parse(tokens):
        output_tokens = []

        current_number = None
        last_number_order = None

        def reset_state():
            nonlocal current_number, last_number_order

            output_tokens.append(current_number)

            current_number = None
            last_number_order = None

        for token in tokens:
            if token not in NUMBER_WORDS:
                if current_number is not None:
                    reset_state()

                output_tokens.append(token)
                continue

            if current_number is None:
                if token in WORD_TO_NUMBERS_ZERO:
                    output_tokens.append(WORD_TO_NUMBERS_ZERO[token])

                elif token in WORD_TO_NUMBERS_1_9:
                    output_tokens.append(WORD_TO_NUMBERS_1_9[token])

                elif token in WORD_TO_NUMBERS_10_19:
                    output_tokens.append(WORD_TO_NUMBERS_10_19[token])

                elif token in WORD_TO_NUMBERS_20_90:
                    current_number = WORD_TO_NUMBERS_20_90[token]
                    last_number_order = 10

                else:  # token in WORD_TO_NUMBERS_100_900
                    current_number = WORD_TO_NUMBERS_100_900[token]
                    last_number_order = 100
            else:
                if token in WORD_TO_NUMBERS_ZERO:
                    reset_state()
                    output_tokens.append(WORD_TO_NUMBERS_ZERO[token])

                elif token in WORD_TO_NUMBERS_1_9:
                    current_number += WORD_TO_NUMBERS_1_9[token]
                    reset_state()

                elif token in WORD_TO_NUMBERS_10_19:
                    if last_number_order == 10:
                        reset_state()
                        output_tokens.append(WORD_TO_NUMBERS_10_19[token])

                    else:  # last_number_order == 100
                        current_number += WORD_TO_NUMBERS_10_19[token]
                        reset_state()

                elif token in WORD_TO_NUMBERS_20_90:
                    if last_number_order == 10:
                        reset_state()
                        output_tokens.append(WORD_TO_NUMBERS_20_90[token])
                    else:  # last_number_order == 100
                        current_number += WORD_TO_NUMBERS_20_90[token]
                        last_number_order = 10

                else:  # token in WORD_TO_NUMBERS_100_900:
                    reset_state()
                    current_number = WORD_TO_NUMBERS_100_900[token]
                    last_number_order = 100

        if current_number is not None:
            reset_state()

        return [str(t) for t in output_tokens]
