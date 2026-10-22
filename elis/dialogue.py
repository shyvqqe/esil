from __future__ import annotations
import re
from elis import followups as elis_followups


IOS_VERSION_PATTERN = re.compile(r"\b(?:ios|айос)\b", re.IGNORECASE)


CURRENT_TIME_PATTERN = re.compile(
    r"\b(?:сколько\s+(?:сейчас\s+)?времени|который\s+час|текущее\s+время)\b",
    re.IGNORECASE,
)


ELIS_CHECKIN_TEXT = (
    r"(?:(?:а\s+)?(?:у\s*тебя(?:\s+как)?|ты\s+как|"
    r"как\s+(?:у\s*тебя(?:\s+дела)?|ты|твои\s+дела|"
    r"дела(?:\s+у\s*тебя)?|настроение(?:\s+(?:у\s*тебя|сегодня))?|"
    r"(?:твой\s+|у\s*тебя\s+)?день(?:\s+(?:у\s*тебя|прош[её]л))?|"
    r"прош[её]л\s+(?:твой\s+)?день|"
    r"поживаешь|жизнь)|что\s+у\s*тебя\s+нового)(?:\s+сегодня)?|а\s+ты)"
)


CASUAL_CHECKIN_PATTERN = re.compile(
    r"^\s*(?:(?:эй\s+)?(?:esil|эсил|эсиль|elis|элис)\b[\s,:;.!?—-]*)?"
    r"(?:(?:привет|здравствуй|здравствуйте)[\s,:;.!?—-]*)?"
    r"(?:а\s+)?(?:как\s+(?:у\s*тебя\s+)?дела|как\s+ты|как\s+поживаешь|"
    r"как\s+настроение|как\s+жизнь)[\s?!.,…]*$",
    re.IGNORECASE,
)


CREATOR_QUESTION_PATTERN = re.compile(
    r"\b(?:"
    r"кто\s+(?:(?:же|вообще)\s+)?(?:твой|ваш|твоя|ваша)\s+(?:создател[ья]|автор|разработчик|владелец|хозяин|создательница)|"
    r"кто\s+(?:тебя|тебе)\s+(?:создал[а-яё]*|сделал[а-яё]*|настроил[а-яё]*|"
    r"написал[а-яё]*|придумал[а-яё]*)|"
    r"кто\s+(?:(?:же|вообще)\s+)?(?:такой\s+|такая\s+)?zev1x|zev1x\s+(?:это\s+кто|кто\s+такой)|"
    r"расскажи\s+(?:мне\s+)?(?:про|о)\s+zev1x|чьё\s+ты\s+создание|"
    r"кто\s+стоит\s+за\s+тобой|кто\s+автор\s+(?:esil|эсил|эсиль|elis|veyr)"
    r")\b",
    re.IGNORECASE,
)


ELIS_GENDER_FORMS = {
    "понял": "поняла",
    "проверил": "проверила",
    "ответил": "ответила",
    "запомнил": "запомнила",
    "сказал": "сказала",
    "сделал": "сделала",
    "нашёл": "нашла",
    "нашел": "нашла",
    "подумал": "подумала",
    "был": "была",
    "готов": "готова",
    "уверен": "уверена",
    "рад": "рада",
    "прав": "права",
    "забыл": "забыла",
    "узнал": "узнала",
    "помог": "помогла",
    "разобрался": "разобралась",
    "подключился": "подключилась",
    "согласен": "согласна",
    "виноват": "виновата",
}


ELIS_MASCULINE_SELF_REFERENCE = re.compile(
    r"(?i)(\bя\s+(?:(?:не|уже|наконец|сразу|наверное|кажется)\s+){0,3})"
    r"(" + "|".join(sorted(ELIS_GENDER_FORMS, key=len, reverse=True)) + r")\b"
)


ELIS_MASCULINE_STANDALONE = re.compile(
    r"(?i)(^|[.!?]\s+|,\s+)(" + "|".join(
        sorted(ELIS_GENDER_FORMS, key=len, reverse=True)
    ) + r")\b"
)


ELIS_PROTECTED_TEXT = re.compile(
    r"(```[\s\S]*?```|`[^`\n]*`|«[^»]*»|“[^”]*”|\"[^\"\n]*\"|"
    r"'[^'\n]*'|^[ \t]*>[^\n]*(?:\n|$))",
    re.MULTILINE,
)


ELIS_GENDER_TOKEN = re.compile(
    r"(?<!\w)(" + "|".join(
        re.escape(form) for form in sorted(ELIS_GENDER_FORMS, key=len, reverse=True)
    ) + r")(?:\((?:а|ла|на|ась|лась)\))?(?!\w)",
    re.IGNORECASE,
)


ELIS_CHECKIN_QUESTION = re.compile(
    ELIS_CHECKIN_TEXT + r"[?!.]*",
    re.IGNORECASE,
)


ELIS_CHECKIN_SUFFIX = re.compile(
    r"(?:[,!.]\s*|\s+)" + ELIS_CHECKIN_TEXT + r"[?!.]*$", re.IGNORECASE,
)


ELIS_GREETING_PREFIX = re.compile(
    r"^\s*(?:привет|здравствуй(?:те)?|добрый\s+(?:день|вечер)|доброе\s+утро)"
    r"\b[\s!.,:;]*", re.IGNORECASE,
)


ELIS_GENERIC_HELP_QUESTION = re.compile(
    r"(?:чем(?:\s+ещё|\s+еще)?\s+(?:я\s+)?(?:могу\s+)?помочь"
    r"(?:\s+тебе)?|что\s+(?:я\s+)?могу\s+для\s+тебя\s+сделать)[?!.]*",
    re.IGNORECASE,
)


ELIS_SERVICE_STAMP = re.compile(
    r"(?im)^[ \t]*(?:\*\*|__)?\[?Сообщение\s+от\s+"
    r"\d{1,2}[./-]\d{1,2}[./-]\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?"
    r"\s+(?:MSK|МСК|UTC\+0?3(?::00)?)\]?(?:\*\*|__)?(?:[ \t]*\r?\n|[ \t]+|$)"
)


def _strip_elis_service_metadata(text: str) -> str:
    """Remove leaked transport headings, while preserving actual quotes and code."""
    def transform(part: str) -> str:
        part = ELIS_SERVICE_STAMP.sub("", part)
        return re.sub(r"(?im)^\s*(?:Собеседник:[^\n]*\n|Сообщение:\s*)", "", part)

    return _elis_unquoted_transform(text, transform).strip()


def _normalize_esil_identity(text: str, *, history: bool = False) -> str:
    """Old assistant turns cannot teach the former name; literal quotes stay intact."""
    def transform(part: str) -> str:
        if history:
            return re.sub(r"\b(?:Elis|Элис)\b", "Esil", part, flags=re.IGNORECASE)
        return re.sub(
            r"(\b(?:я|меня\s+зовут|мо[её]\s+имя)\s*(?:[—–:-]\s*)?)(?:Elis|Элис)\b",
            lambda match: match.group(1) + "Esil", part, flags=re.IGNORECASE,
        )

    return _elis_unquoted_transform(text, transform)


def _elis_unquoted_transform(text: str, transform) -> str:
    """Keep quoted words, Discord block quotes and code exactly as supplied."""
    return "".join(
        part if index % 2 else transform(part)
        for index, part in enumerate(ELIS_PROTECTED_TEXT.split(text))
    )


def _use_elis_feminine_self_reference(text: str) -> str:
    def transform(part: str) -> str:
        def replace(match: re.Match) -> str:
            start = max(part.rfind(mark, 0, match.start()) for mark in (".", "!", "?", "\n", ";")) + 1
            prefix = re.sub(r"[*_~]", "", part[start:match.start()]).strip().lower()
            subjects = list(re.finditer(r"\b(?:я|ты|вы|он|она|они|мы)\b", prefix))
            suffix = part[match.end():]
            # "Ты готов(а)?" and "Готов ли ты?" describe the interlocutor.
            if re.match(r"\s+(?:(?:ли|же)\s+)?(?:ты|вы|он|она|они|мы)\b", suffix, re.IGNORECASE):
                return match.group(0)
            if subjects:
                if subjects[-1].group(0) != "я":
                    return match.group(0)
            elif not re.fullmatch(
                r"(?:(?:не|уже|ещё|еще|тоже|очень|совсем|вполне|наконец|"
                r"сразу|наверное|кажется|спасибо|да|ага|ну|ок|извини)\b[\s,:]*)*",
                prefix,
            ):
                return match.group(0)
            original = match.group(1)
            feminine = ELIS_GENDER_FORMS[original.lower()]
            if original.isupper():
                return feminine.upper()
            return feminine.capitalize() if original[:1].isupper() else feminine

        return ELIS_GENDER_TOKEN.sub(replace, part)

    return _elis_unquoted_transform(text, transform)


def _elis_dialogue_user_text(value) -> str:
    if not isinstance(value, str):
        return ""
    if "\nСообщение: " in value:
        value = value.split("\nСообщение: ", 1)[1]
    value = re.sub(r"<@!?\d+>", "", value)
    value = _strip_elis_service_metadata(value)
    value = re.sub(r"^\s*(?:esil|эсил|эсиль|elis|элис)\b[\s,:;.!?—-]*", "", value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", value).strip()


def _elis_mood_answer(value: str) -> bool:
    text = _elis_dialogue_user_text(value).lower()
    text = ELIS_CHECKIN_SUFFIX.sub("", text).strip(" ,.!?")
    simple_answer = bool(re.fullmatch(
        r"(?:(?:да|ну|всё|все|я|сегодня|у\s+меня|спасибо|пока|вроде)\s*[,!]?\s*)*"
        r"(?:хорошо|нормально|норм|отлично|неплохо|супер|плохо|так\s+себе|"
        r"замечательно|прекрасно|устал[а]?|грустно|нормас)(?:\s*[,!]\s*спасибо)?",
        text,
    ))
    if simple_answer:
        return True
    # People often mention their day before asking back, without punctuation.
    return bool(re.fullmatch(
        r"(?:(?:у\s+меня|мой|сегодня|сегодняшний|очень)\s+)*"
        r"(?:(?:хороший|отличный|прекрасный|неплохой|нормальный|суперский|"
        r"плохой|тяж[её]лый|ужасный|спокойный)\s+(?:день|вечер)|"
        r"(?:хорошее|отличное|плохое|ужасное)\s+настроение|"
        r"день\s+(?:прош[её]л\s+)?(?:хорошо|отлично|нормально|плохо))"
        r"(?:\s+(?:у\s+меня|сегодня|спасибо))*",
        text,
    ))


def _elis_recent_mood_answer(prior_history: list[dict]) -> bool:
    # A technical follow-up must not inherit an older, already finished check-in.
    for item in reversed(prior_history[-8:]):
        if item.get("role") == "user":
            return _elis_mood_answer(item.get("content", ""))
    return False


def _elis_conversation_instruction(incoming: str, prior_history: list[dict], *,
                                   reply_context: str = "") -> str:
    """Narrow hints for the current conversational turn, without invented facts."""
    text = _elis_dialogue_user_text(incoming)
    if _elis_mood_answer(text):
        return (
            "Собеседник уже рассказал о своём состоянии в текущем сообщении. "
            "Не спрашивай снова «а у тебя как?» или «как настроение?». Если он спросил "
            "о тебе, сначала ответь на это. Не начинай заново приветствие, не переводи "
            "обычный разговор в «чем могу помочь?». Короткое подтверждение может быть "
            "полноценным ответом без нового вопроса. Пиши «рада», без «рад(а)»."
        )
    if _elis_recent_mood_answer(prior_history) and ELIS_CHECKIN_QUESTION.fullmatch(text.strip(" ,")):
        return (
            "Собеседник спрашивает о тебе и уже рассказал о своём состоянии ранее. "
            "Ответь на его вопрос коротко; не задавай ему тот же вопрос повторно. "
            "Не добавляй обязательное приглашение к помощи или новое приветствие."
        )
    return elis_followups.followup_instruction(incoming, prior_history, reply_context=reply_context)


def _elis_casual_checkin_reply(incoming: str, prior_history: list[dict]) -> str:
    variants = ("Всё хорошо, спасибо.", "У меня всё спокойно, я на связи.",
                "Я в порядке, рада поболтать.")
    previous = [item.get("content", "") for item in prior_history[-6:]
                if item.get("role") == "assistant"]
    answer = next((text for text in variants if not any(text in old for old in previous)), variants[0])
    if _elis_mood_answer(incoming) or _elis_recent_mood_answer(prior_history):
        return answer
    return answer + " А у тебя?"


def _finish_elis_reply(reply: str, incoming: str, prior_history: list[dict]) -> str:
    reply = _use_elis_feminine_self_reference(
        _normalize_esil_identity(_strip_elis_service_metadata(reply)),
    )
    if not (_elis_mood_answer(incoming) or (
        _elis_recent_mood_answer(prior_history)
        and ELIS_CHECKIN_QUESTION.fullmatch(_elis_dialogue_user_text(incoming).strip(" ,"))
    )):
        return reply or "Кажется, я потеряла мысль. Напиши ещё раз?"

    # Strip a repeated greeting only in a recognized continuation of a check-in.
    if any(item.get("role") == "assistant" for item in prior_history) and not (
        ELIS_GREETING_PREFIX.match(_elis_dialogue_user_text(incoming))
    ):
        reply = ELIS_GREETING_PREFIX.sub("", reply, count=1).strip() or "Поняла тебя."

    def remove_generic_followups(part: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+|\n+", part)
        return " ".join(
            sentence for sentence in sentences
            if not ELIS_CHECKIN_QUESTION.fullmatch(sentence.strip(" *_"))
            and not ELIS_GENERIC_HELP_QUESTION.fullmatch(sentence.strip(" *_"))
        )

    finished = _elis_unquoted_transform(reply, remove_generic_followups).strip()
    return finished or "Поняла тебя."
