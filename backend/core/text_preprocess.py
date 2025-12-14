import re
from typing import List, Set


class TextPreprocessor:
    RUS_STOP: Set[str] = {
        'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она', 'так', 'его',
        'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от',
        'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже',
        'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там', 'потом',
        'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их',
        'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда',
        'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь', 'этом', 'один', 'почти', 'мой',
        'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец',
        'два', 'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего',
        'них', 'какая', 'много', 'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда',
        'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между', 'всё', 'это', 'текст'
    }
    ENG_STOP: Set[str] = {
        'the', 'and', 'is', 'in', 'at', 'of', 'a', 'to', 'it', 'for', 'on', 'with', 'as', 'by', 'an', 'be', 'are',
        'this', 'that', 'from', 'or', 'but', 'not', 'was', 'were', 'have', 'has', 'had', 'you', 'we', 'they', 'he',
        'she', 'them', 'his', 'her', 'their', 'our', 'us', 'i', 'me', 'my', 'your', 'yours', 'about', 'into', 'over',
        'after', 'before', 'between', 'out', 'up', 'down', 'so', 'no', 'if', 'can', 'will', 'just', 'than', 'then',
        'there', 'here', 'also', 'more', 'most', 'such', 'only', 'other', 'some', 'any', 'each', 'few', 'because',
        'how', 'why', 'what', 'which', 'who', 'whom', 'when', 'where'
    }
    STOP_WORDS: Set[str] = RUS_STOP | ENG_STOP

    WORD_ENDINGS: List[str] = [
        'ться', 'ешься', 'ится', 'ется', 'аются', 'яются', 'ются',
        'ами', 'ями', 'ьми',
        'ах', 'ях', 'ьях',
        'ам', 'ям', 'ьям',
        'ов', 'ев', 'ей', 'ий', 'ьев', 'ьей',
        'ую', 'юю',
        'ой', 'ей', 'ою', 'ею', 'ым', 'им',
        'ого', 'его', 'ых', 'их',
        'ые', 'ие',
        'ый', 'ий', 'ая', 'яя', 'ое', 'ее',
        'ешь', 'ете', 'ет', 'ут', 'ют', 'ишь', 'ите', 'ит', 'ат', 'ят',
        'уть', 'ить', 'еть', 'ать', 'оть', 'ыть',
        'ал', 'ала', 'али', 'ало', 'ела', 'ели', 'ело', 'ил', 'ила', 'или', 'ило',
        'ул', 'ула', 'ули', 'уло',
        'щий', 'щая', 'щее', 'щие', 'вший', 'вшая', 'вшее', 'вшие',
        'ся', 'сь',
        'я', 'а', 'о', 'е', 'и', 'ы', 'у', 'ю'
    ]
    WORD_ENDINGS_SORTED: List[str] = sorted(WORD_ENDINGS, key=len, reverse=True)

    @staticmethod
    def stem(word: str) -> str:
        if len(word) < 4:
            return word
        w = re.sub(r'(.)\1+', r'\1', word)
        for ending in TextPreprocessor.WORD_ENDINGS_SORTED:
            if w.endswith(ending) and len(w) - len(ending) >= 3:
                return w[:-len(ending)]
        return w

    @staticmethod
    def preprocess(text: str) -> str:
        if not isinstance(text, str) or not text:
            return ""
        t = text.lower().replace('ё', 'е')
        t = re.sub(r'[^a-zа-я\s]', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        if not t:
            return ""
        words = [w for w in t.split() if len(w) > 2 and w not in TextPreprocessor.STOP_WORDS]
        stems = [TextPreprocessor.stem(w) for w in words]
        stems = [w for w in stems if len(w) > 1]
        return ' '.join(stems).strip()


def preprocess_text(text: str) -> str:
    return TextPreprocessor.preprocess(text)


# Дополнительные стоп-слова для пользовательских запросов (интент-слова)
QUERY_EXTRA_STOP: Set[str] = {
    'хочу', 'изучить', 'изучать', 'ищу', 'искать', 'нужно', 'надо',
    'подскажите', 'пожалуйста', 'помоги', 'помогите', 'найти',
    'расскажите', 'посоветуйте', 'интересует', 'прошу'
}


def preprocess_query(text: str) -> str:
    if not isinstance(text, str) or not text:
        return ""
    t = text.lower().replace('ё', 'е')
    t = re.sub(r'[^a-zа-я\s]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    if not t:
        return ""
    stop = TextPreprocessor.STOP_WORDS | QUERY_EXTRA_STOP
    words = [w for w in t.split() if len(w) > 2 and w not in stop]
    stems = [TextPreprocessor.stem(w) for w in words]
    stems = [w for w in stems if len(w) > 1]
    return ' '.join(stems).strip()
