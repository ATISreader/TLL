import os
import json
import sys
import re
from groq import Groq
from faster_whisper import WhisperModel
from dictionary import replacement_dict

def run_atis_system():
    audio_file = "atis_recorded.wav"
    template_path = "template.html"
    index_path = "index.html"

    if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
        print(">>> ERREUR: Fichier audio manquant.")
        sys.exit(1)

    # 1. Transcription avec Whisper Medium (Meilleur compromis précision/vitesse)
    print(">>> CHARGEMENT DU MODÈLE : medium...")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    
    print(">>> TRANSCRIPTION EN COURS...")
    segments, _ = model.transcribe(audio_file)
    
    # 2. Dédoublonnage et concaténation
    unique_segments = []
    seen = set()
    for segment in segments:
        text = segment.text.strip()
        if text not in seen and len(text) > 3:
            unique_segments.append(text)
            seen.add(text)
    transcription = " ".join(unique_segments).upper()
    
    # 3. Application du dictionnaire
    for erreur, correction in replacement_dict.items():
        transcription = transcription.replace(erreur.upper(), correction.upper())
    
    # 4. Extraction du bloc unique (Regex : de "THIS IS TALLINN" à la prochaine occurrence)
    pattern = r"(THIS IS TALLINN.*?)(?=THIS IS TALLINN|$)"
    match = re.search(pattern, transcription, re.IGNORECASE | re.DOTALL)
    clean_transcription = match.group(1).strip() if match else transcription

    # 5. Analyse Groq
    print(">>> ANALYSE AVEC GROQ (LLAMA-3.3)...")
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    prompt = f"""
    Analyze this ATIS transcription. Return a JSON object ONLY.
    - INFO: Extract ONLY the single letter (e.g. "E").
    - ZULU: Extract time as HH:MM.
    - RWY: Return exactly "26 IN USE".
    - WIND, QNH, RVR, TEMP_DEWP, RCC, CONTAM: Extract clear values.
    - RAW_TEXT: The provided transcription.
    
    Transcription: {clean_transcription}
    """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(completion.choices[0].message.content)
    
    # 6. Nettoyage final pour garantir le format visuel souhaité
    data["INFO"] = data.get("INFO", "").replace("INFORMATION", "").strip()
    data["RWY"] = "26 IN USE"
    data["RAW_TEXT"] = clean_transcription

    # 7. Injection dans le template HTML
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # On remplace les placeholders par les valeurs du dictionnaire 'data'
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", str(value))
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(">>> SUCCÈS : Dashboard mis à jour avec le modèle medium.")

if __name__ == "__main__":
    run_atis_system()
