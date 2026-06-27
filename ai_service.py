import os
import json
import re
from google import genai
from google.genai import types
from groq import Groq


def clean_json_response(text: str) -> str:
    """Extract JSON from markdown code blocks if the model wrapped it."""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def summarize_content(content: str, provider: str, api_key: str) -> str:
    """Generate a concise educational summary using Gemini or Groq."""
    if not api_key or api_key.strip() == "":
        return (
            f"[MOCK ÖZET - API Anahtarı Girilmedi]\n"
            "Bu ders, temel kavramları ve önemli noktaları ele almaktadır. "
            f"API anahtarınızı girerek LLM ({provider.upper()}) tarafından oluşturulmuş gerçek bir özet alabilirsiniz.\n\n"
            f"İçeriğin ilk 100 karakteri: {content[:100]}..."
        )

    prompt = (
        "Sen deneyimli bir öğretmensin. Lütfen aşağıdaki ders içeriğini öğrenciler için anlaşılır, "
        "önemli noktaları vurgulayan ve yapılandırılmış kısa bir özet haline getir. "
        "Yalnızca Türkçe yanıt ver.\n\n"
        f"Ders İçeriği:\n{content}"
    )

    try:
        if provider.lower() == "gemini":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()

        elif provider.lower() == "groq":
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Sen yardımcı ve uzman bir eğitim asistanısın."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            return completion.choices[0].message.content.strip()

        else:
            return "Geçersiz LLM sağlayıcısı seçildi."

    except Exception as e:
        return f"Özet oluşturulurken bir hata oluştu ({provider}): {str(e)}"


def analyze_submission(lesson_content: str, student_submission: str, provider: str, api_key: str) -> dict:
    """Evaluate a student's answer using Gemini or Groq, returning feedback and a grade."""
    default_feedback = {
        "feedback": (
            "[MOCK GERİ BİLDİRİM - API Anahtarı Yok ya da Hata Oluştu]\n"
            "Yazınız teslim alındı. Ders içeriğine uygunluğu ve anlatımı genel olarak başarılı. "
            "API anahtarınızı girerek yapay zeka tarafından detaylı analiz ve notlandırma alabilirsiniz."
        ),
        "grade": 80
    }

    if not api_key or api_key.strip() == "":
        return default_feedback

    prompt = (
        "Sen adil ve yapıcı bir öğretmensin. Aşağıdaki ders içeriğini referans alarak öğrencinin "
        "gönderdiği yazıyı veya ödevi değerlendir.\n"
        "Öğrenciye neyi iyi yaptığını, nereleri geliştirebileceğini açıklayan detaylı, yapıcı ve samimi "
        "bir geri bildirim (feedback) yaz. Ayrıca 100 üzerinden bir not (grade) ver.\n\n"
        "ÖNEMLİ: Yanıtını mutlaka aşağıdaki JSON şablonunda döndür. Başka hiçbir açıklama ekleme.\n"
        "{\n"
        '  "feedback": "Detaylı geri bildirim metniniz burada (Türkçe).",\n'
        '  "grade": 85\n'
        "}\n\n"
        f"DERS İÇERİĞİ:\n{lesson_content}\n\n"
        f"ÖĞRENCİ YAZISI:\n{student_submission}"
    )

    try:
        if provider.lower() == "gemini":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            clean_txt = clean_json_response(response.text)
            return json.loads(clean_txt)

        elif provider.lower() == "groq":
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educator. Respond ONLY with a valid JSON object with 'feedback' (string, Turkish) and 'grade' (integer 0-100)."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            clean_txt = clean_json_response(completion.choices[0].message.content)
            return json.loads(clean_txt)

        else:
            return default_feedback

    except Exception as e:
        print(f"AI Analiz Hatasi ({provider}): {str(e)}")
        return {
            "feedback": f"Yapay zeka analiz yaparken bir hata ile karşılaştı: {str(e)}",
            "grade": 0
        }
