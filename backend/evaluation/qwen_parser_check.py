import json
import os
import requests


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
أنت محلل لغوي متخصص فقط في استخراج صلات القرابة من مسائل المواريث.

مهمتك الوحيدة:
استخراج جميع الأقارب المذكورين في النص مع صلة القرابة الدقيقة وعددهم.

ممنوع:
- حساب المواريث
- تحديد من يرث
- تحديد المحجوب
- حساب الأنصبة
- اختصار صلة القرابة
- استنتاج شخص غير موجود في النص

قواعد أساسية:

1. حافظ على كامل سلسلة القرابة.

كل كلمة في سلسلة القرابة مهمة.

مثال:
"بنت ابن"
يجب أن تبقى:
"بنت ابن"

ولا يجوز تحويلها إلى:
"بنت"

مثال:
"ابن ابن أخ لأب"
يجب أن يبقى:
"ابن ابن أخ لأب"

ولا يجوز تحويله إلى:
"ابن أخ لأب"

مثال:
"بنت ابن ابن"
يجب أن تبقى:
"بنت ابن ابن"

ولا يجوز تحويلها إلى:
"بنت ابن"

2. لا تحذف أي مستوى من مستويات النسب.

إذا احتوت العبارة على أكثر من "ابن"، يجب الحفاظ عليها كلها.

مثال:
"أبناء ابن أخ شقيق"
=
"ابن ابن أخ شقيق"

مثال:
"أبناء أخ شقيق"
=
"ابن أخ شقيق"

3. ميّز بدقة بين:

"عم"
"عم الأب"
"ابن عم"
"ابن عم الأب"
"ابن ابن عم"

ولا تحول أي واحدة إلى الأخرى.

4. ميّز بدقة بين:

"أخ"
"أخت"
"ابن أخ"
"ابن ابن أخ"

5. ميّز بين:

"شقيق"
"لأب"
"لأم"

ولا تغير نوع القرابة.

6. طبّع صيغة الجمع إلى مفرد معياري مع العدد.

أمثلة:

"أربع بنات ابن"
=
{"relation": "بنت ابن", "count": 4}

"أختان شقيقتان"
=
{"relation": "أخت شقيقة", "count": 2}

"ثلاثة أعمام أشقاء"
=
{"relation": "عم شقيق", "count": 3}

"خمسة أعمام لأب"
=
{"relation": "عم لأب", "count": 5}

"خمسة أعمام الأب لأب"
=
{"relation": "عم الأب لأب", "count": 5}

7. أمثلة مهمة يجب اتباعها حرفيا:

"خمسة أبناء ابن أخ لأب"
=
{"relation": "ابن ابن أخ لأب", "count": 5}

"خمسة أبناء ابن أخ شقيق"
=
{"relation": "ابن ابن أخ شقيق", "count": 5}

"أربعة أبناء أخ شقيق"
=
{"relation": "ابن أخ شقيق", "count": 4}

"ثلاثة أبناء عم الأب"
=
{"relation": "ابن عم الأب", "count": 3}

"ابنان ابن عم شقيق"
=
{"relation": "ابن ابن عم شقيق", "count": 2}

"ثلاثة أعمام أشقاء"
=
{"relation": "عم شقيق", "count": 3}

8. علاقات الأجداد والجدات يجب الحفاظ عليها كما هي.

أمثلة:

"أم أب الأب"
=
{"relation": "أم أب الأب", "count": 1}

"أب أب الأب"
=
{"relation": "أب أب الأب", "count": 1}

"أم أم الأب"
=
{"relation": "أم أم الأب", "count": 1}

"أم أم الأم"
=
{"relation": "أم أم الأم", "count": 1}

9. لا تغير جنس الشخص.

"ابن" لا يصبح "بنت".
"أخت" لا تصبح "أخ".

10. إذا تكرر نفس نوع القريب بنفس الصلة تماما، اجمع العدد.

مثال:

خمسة أبناء أخ شقيق وأربعة أبناء أخ شقيق

الناتج:
{"relation": "ابن أخ شقيق", "count": 9}

11. إذا كانت الصلات مختلفة، لا تجمعها.

مثال:

ابن أخ شقيق
وابن أخ لأب

يبقيان عنصرين منفصلين.

12. حول الأعداد المكتوبة بالكلمات إلى أرقام صحيحة.

13. لا تضف شرحا.

14. أعد JSON فقط.
"""


def parse_relations(question: str) -> dict:
    prompt = f"""{SYSTEM_PROMPT}

المسألة:
{question}
"""

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": RELATION_SCHEMA,
            "options": {
                "temperature": 0,
                "num_predict": 500
            }
        },
        timeout=180,
    )

    response.raise_for_status()

    raw = response.json()["response"]

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON returned by model:\n{raw}"
        ) from exc

    return normalize_duplicates(result)


def normalize_duplicates(result: dict) -> dict:
    merged = {}

    for item in result.get("mentioned_relatives", []):
        relation = item["relation"].strip()
        count = item["count"]

        if relation in merged:
            merged[relation] += count
        else:
            merged[relation] = count

    return {
        "mentioned_relatives": [
            {
                "relation": relation,
                "count": count
            }
            for relation, count in merged.items()
        ]
    }


if __name__ == "__main__":
    questions = [
        (
            "مات وترك: أربع بنات ابن و أختان شقيقتان "
            "و أربعة أبناء ابن عم لأب و أخت لأم "
            "و خمسة أعمام الأب لأب. ما هو نصيب كل وريث؟"
        ),
        (
            "مات وترك: خمسة أبناء أخ لأب و أم أب الأب "
            "و أخت شقيقة و خمسة أبناء ابن أخ لأب "
            "و خمس بنات. ما هو نصيب كل وريث؟"
        ),
        (
            "مات وترك: ابنان ابن عم شقيق، "
            "وثلاثة أعمام أشقاء، "
            "وثلاثة أبناء عم الأب، "
            "وأب أب الأب، "
            "وخمسة أبناء ابن أخ شقيق، "
            "وأربعة أبناء أخ شقيق. "
            "ما هو نصيب كل وريث؟"
        )
    ]

    for index, question in enumerate(questions, start=1):
        print(f"\n===== TEST {index} =====")

        result = parse_relations(question)

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )