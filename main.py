import os
import json
import sys
from groq import Groq
from faster_whisper import WhisperModel
from dictionary import replacement_dict

def run_atis_system():
    audio_file = "atis_recorded.wav"
    template_path = "template.html"
    index_path = "index.html"

    if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
        sys.exit(1)

    # 1. Transcription avec Whisper Small
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_file)
    
    # 2. Dédoublonnage : on ne garde qu'une seule occurrence de chaque phrase unique
    seen = set()
    unique_segments = []
    for segment in segments:
        text = segment.text.strip()
        if text not in seen and len(text) > 3:
            unique_segments.append(text)
            seen.add(text)
    transcription = " ".join(unique_segments).upper()
    
    # 3. Nettoyage avec dictionnaire
    for erreur, correction in replacement_dict.items():
        transcription = transcription.replace(erreur.upper(), correction.upper())
    
    # 4. Analyse Groq avec contrainte de Majuscules
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"""
    Analyze this ATIS. Provide ALL output values in UPPERCASE ENGLISH.
    Return ONLY a JSON object.
    Transcription: {transcription}
    
    Format:
    {{
        "INFO": "INFO LETTER",
        "ZULU": "TIME HH:MM",
        "RWY": "RWY AND STATUS",
        "QNH": "QNH VALUE",
        "WIND": "WIND DIRECTION/SPEED",
        "RVR": "VISIBILITY",
        "TEMP_DEWP": "TEMP/DEWPOINT",
        "RCC": "RCC CODE",
        "CONTAM": "CONTAMINANTS",
        "RAW_TEXT": "SINGLE PASS TRANSCRIPTION"
    }}
    """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(completion.choices[0].message.content)
    
    # 5. Nettoyage final : forcer toutes les valeurs en majuscules
    for key in data:
        data[key] = str(data[key]).upper()

    # 6. Injection dans le template
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", value)
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    run_atis_system()
