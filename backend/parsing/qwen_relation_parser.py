import json
import os
import requests
from backend.llm.generation_capacity import generation_post


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")


RELATION_SCHEMA = {
    "type": "object",
    "properties": {
        "mentioned_relatives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "relation": {
                        "type": "string"
                    },
                    "count": {
                        "type": "integer"
                    }
                },
                "required": [
                    "relation",
                    "count"
                ]
            }
        }
    },
    "required": [
        "mentioned_relatives"
    ]
}


SYSTEM_PROMPT = """
أنت محلل لغوي متخصص في استخراج صلات القرابة من مسائل المواريث.

مهمتك الوحيدة هي استخراج جميع الأشخاص المذكورين في المسألة مع صلة القرابة الدقيقة وعددهم.

ممنوع حساب المواريث.
ممنوع تحديد من يرث.
ممنوع تحديد المحجوب.
ممنوع حساب الأنصبة.

قواعد مهمة جدا:

1. حافظ على صلة القرابة كاملة ولا تختصرها.

أمثلة:

"بنت ابن" تبقى:
بنت ابن

ولا تتحول إلى:
بنت

"ابن ابن عم لأب" يبقى:
ابن ابن عم لأب

ولا يتحول إلى:
ابن

"أم أب الأب" تبقى:
أم أب الأب

"أب أب الأب" يبقى:
أب أب الأب

"ابن أخ شقيق" يبقى:
ابن أخ شقيق

"ابن عم شقيق" يبقى:
ابن عم شقيق

"عم الأب لأب" يبقى:
عم الأب لأب

2. لا تستنتج أقارب غير موجودين في النص.

3. لا تغير جنس الشخص.

4. اجمع الأقارب المتطابقين تماما في عنصر واحد.

5. حول الأعداد المكتوبة بالكلمات إلى أرقام.

أمثلة:

أربع بنات ابن
=
{"relation": "بنت ابن", "count": 4}

أختان شقيقتان
=
{"relation": "أخت شقيقة", "count": 2}

خمسة أعمام الأب لأب
=
{"relation": "عم الأب لأب", "count": 5}

6. لا تضف شرحا.

7. أعد JSON فقط.

8. أعد اسم صلة القرابة المفرد بصيغته الأساسية، مع إزالة علامة الإعراب.
"أما" أو "أماً" في سياق "ترك زوجة وأما" تعني "أم"، ولا تعني "أمة".
"ابنين" تعني {"relation": "ابن", "count": 2}.
مثال كامل:
"مات وترك زوجة وأما وابنين وبنت. ما هو نصيب كل وريث؟"
يعطي:
{"mentioned_relatives": [{"relation": "زوجة", "count": 1}, {"relation": "أم", "count": 1}, {"relation": "ابن", "count": 2}, {"relation": "بنت", "count": 1}]}
"""


def parse_relations(question: str) -> dict:
    prompt = f"""{SYSTEM_PROMPT}

المسألة:
{question}
"""

    response = generation_post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": RELATION_SCHEMA,
            "options": {
                "temperature": 0,
                "num_predict": 400
            }
        },
        timeout=180,
    )

    response.raise_for_status()

    raw = response.json()["response"]

    try:
        return json.loads(raw)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON returned by model:\n{raw}"
        ) from exc


if __name__ == "__main__":

    question = (
        "مات وترك: أربع بنات ابن و أختان شقيقتان "
        "و أربعة أبناء ابن عم لأب و أخت لأم "
        "و خمسة أعمام الأب لأب. ما هو نصيب كل وريث؟"
    )

    result = parse_relations(question)

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )
