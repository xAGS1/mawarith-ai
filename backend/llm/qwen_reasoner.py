import json
import os
import requests


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

DEBUG_THINKING = False


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "heirs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heir": {"type": "string"},
                    "count": {"type": "integer"},
                },
                "required": ["heir", "count"],
            },
        },
        "blocked": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heir": {"type": "string"},
                    "count": {"type": "integer"},
                },
                "required": ["heir", "count"],
            },
        },
        "shares": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heir": {"type": "string"},
                    "count": {"type": "integer"},
                    "fraction": {"type": "string"},
                },
                "required": ["heir", "count", "fraction"],
            },
        },
        "awl_or_radd": {
            "type": "string",
        },
        "post_tasil": {
            "type": "object",
            "properties": {
                "distribution": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "heir": {"type": "string"},
                            "count": {"type": "integer"},
                            "per_head_shares": {"type": "string"},
                        },
                        "required": [
                            "heir",
                            "count",
                            "per_head_shares",
                        ],
                    },
                }
            },
            "required": ["distribution"],
        },
    },
    "required": [
        "heirs",
        "blocked",
        "shares",
        "awl_or_radd",
        "post_tasil",
    ],
}


SYSTEM_PROMPT = """
أنت نظام متخصص في حل مسائل المواريث الإسلامية.

حل المسألة وأعد النتيجة وفق JSON Schema المحدد فقط.

المدخل المنظم parsed_relations هو المرجع المعتمد الوحيد للأقارب وأعدادهم.
لا تعِد استخراج الأقارب من السؤال، ولا تضف أو تغير الأقارب أو أعدادهم.
السؤال الأصلي للسياق فقط، وليس لتجاوز المدخل المنظم.
استخدم القواعد المسترجعة sources كسياق الاستدلال والتوثيق.
القواعد المسترجعة هي المرجع الوحيد المعتمد للأحكام الشرعية والأنصبة.
لا تستنتج الأنصبة من ذاكرة النموذج عند غياب قاعدة في المصادر المسترجعة.
لا تنشئ أحكاما غير مدعومة بالمصادر المسترجعة ولا تختلق استشهادات.
فحص التغطية البرمجي في Python هو البوابة المعتمدة قبل تشغيل الاستدلال.
لا تخترع مصادر أو مراجع أو روابط، ولا تستخدم قواعد غير موجودة في sources.
إذا كانت القواعد المسترجعة غير كافية لحل المسألة، فلا تخمن الأنصبة:
أعد heirs وblocked وshares وpost_tasil.distribution فارغة، وawl_or_radd = "قواعد غير كافية".

case_features تصف حقائق الحالة فقط ولا تمثل أحكاما شرعية.
كسور shares التي يولدها النموذج مؤقتة، وستستبدلها Python من نصيب الفرد وعدده.

قواعد الإخراج:

1. استخدم أسماء الورثة بالعربية.

2. اجمع الورثة من النوع نفسه في عنصر واحد.
مثال:
ابنان = {"heir": "ابن", "count": 2}

3. heirs تحتوي فقط على الورثة المستحقين.

4. blocked تحتوي فقط على المذكورين في المسألة الذين لا يرثون بسبب الحجب.

5. shares تعرض نصيب المجموعة كاملة من أصل التركة.
مثال:
إذا كان هناك ابنان، ولكل ابن 17/60،
فنصيب مجموعة الابنين هو 17/30.

6. post_tasil.distribution تعرض نصيب كل فرد بعد التصحيح.

7. استخدم الكسور بصيغة نصية مثل:
"1/6"
"17/60"
"2/3"

8. إذا لم يوجد عول أو رد فاستخدم:
"لا"

9. لا تحسب total_shares.
سيتم حسابه برمجيا بعد ذلك.

10. لا تحسب النسب المئوية.
سيتم حسابها برمجيا.

11. لا تضف شرحا أو Markdown أو نصا خارج JSON.

12. تأكد أن نصيب كل فرد في post_tasil.distribution هو نصيب الفرد، وليس نصيب المجموعة.

13. احسب الباقي بطرح مجموع الفروض من 1. عند اجتماع الأبناء والبنات،
عدد وحدات الباقي = 2 * عدد الأبناء + عدد البنات.
نصيب كل بنت = الباقي / عدد الوحدات، ونصيب كل ابن = ضعف نصيب كل بنت.
تحقق أن مجموع (نصيب الفرد * عدد الأفراد) لجميع الورثة يساوي 1.

14. يجب أن يظهر كل وارث مستحق في heirs وفي shares وفي post_tasil.distribution،
بما في ذلك أصحاب الفروض والأبناء والبنات. لا تقتصر shares على الفروض،
ولا تقتصر post_tasil.distribution على أصحاب الباقي.

مثال حسابي للقواعد الثلاث عند وجود زوجة وأم وابنين وبنت:
الزوجة = 1/8، الأم = 1/6، الباقي = 1 - 1/8 - 1/6 = 17/24.
وحدات الباقي = 2 * 2 + 1 = 5.
لكل ابن = (17/24) * 2/5 = 17/60، للبنت = (17/24) * 1/5 = 17/120.
shares: الزوجة 1/8، الأم 1/6، مجموعة الابنين 17/30، البنت 17/120.
post_tasil.distribution: الزوجة count=1 وper_head_shares="1/8"،
الأم count=1 وper_head_shares="1/6"، الابن count=2 وper_head_shares="17/60"،
البنت count=1 وper_head_shares="17/120".
هذه كسور من أصل التركة كاملة وليست من الباقي وحده.
"""


def generate_raw(question: str, parsed_relations: dict, case_features: dict, sources: list) -> str:
    prompt = f"""{SYSTEM_PROMPT}

المسألة:
{question}

parsed_relations (authoritative):
{json.dumps(parsed_relations, ensure_ascii=False)}

case_features (shared factual features):
{json.dumps(case_features, ensure_ascii=False)}

sources (condition-matched rules and source metadata):
{json.dumps(sources, ensure_ascii=False)}
"""

    if DEBUG_THINKING:
        with requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": True,
                "think": True,
                "format": OUTPUT_SCHEMA,
                "options": {
                    "temperature": 0
                },
            },
            stream=True,
            timeout=300,
        ) as response:

            response.raise_for_status()

            final_text = ""

            print("\n--- THINKING ---\n")

            for line in response.iter_lines():
                if not line:
                    continue

                chunk = json.loads(line.decode("utf-8"))

                thinking = chunk.get("thinking")
                if thinking:
                    print(
                        thinking,
                        end="",
                        flush=True,
                    )

                content = chunk.get("response")
                if content:
                    final_text += content

            print("\n\n--- FINAL JSON ---\n")

            return final_text

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": OUTPUT_SCHEMA,
            "options": {
                "temperature": 0
            },
        },
        timeout=300,
    )

    response.raise_for_status()

    return response.json()["response"]


def analyze_case(question: str, parsed_relations: dict, case_features: dict, sources: list) -> dict:
    """Return model JSON; shared pipeline verification runs separately."""
    raw = generate_raw(question, parsed_relations, case_features, sources)

    try:
        result = json.loads(raw)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model returned invalid JSON:\n{raw}"
        ) from exc

    return result


if __name__ == "__main__":
    from backend.pipeline.qwen_pipeline import run_pipeline

    example = (
        "مات وترك زوجة وأما وابنين وبنت. "
        "ما هو نصيب كل وريث؟"
    )

    result = run_pipeline(example)["result"]

    with open(
        "qwen_output.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("Saved result to qwen_output.json")
