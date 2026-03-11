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

    # 1. Transcription avec Whisper Medium
    print(">>> CHARGEMENT DU MODÈLE : medium...")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    
    print(">>> TRANSCRIPTION EN COURS...")
    segments, _ = model.transcribe(audio_file)
    
    unique_segments = []
    seen = set()
    for segment in segments:
        text = segment.text.strip()
        if text not in seen and len(text) > 3:
            unique_segments.append(text)
            seen.add(text)
    transcription = " ".join(unique_segments).upper()
    
    # 2. Application du dictionnaire
    for erreur, correction in replacement_dict.items():
        transcription = transcription.replace(erreur.upper(), correction.upper())
    
    # 3. Extraction du bloc unique
    pattern = r"(THIS IS TALLINN.*?)(?=THIS IS TALLINN|$)"
    match = re.search(pattern, transcription, re.IGNORECASE | re.DOTALL)
    clean_transcription = match.group(1).strip() if match else transcription

    # 4. Analyse Groq
    print(">>> ANALYSE AVEC GROQ (LLAMA-3.3)...")
    client = Groq(api_key=os.environ.get("GROQ_KEY"))
    prompt = f"""
    You are an aviation expert. Analyze this ATIS. Return ONLY a JSON object.
    - INFO: Extract ONLY the letter (e.g. "D").
    - ZULU: Extract time as HH:MM.
    - RWY: "26 IN USE".
    - WIND: Extract clear values (e.g. 190°, 9 KNOTS). If multiple, list them.
    - RVR: Extract visibility or "NONE".
    - TEMP_DEWP: Extract format (e.g. 11, 3).
    - RCC: Format as X, X, X.
    - CONTAM: Extract percentage and state (e.g. "25% WET, 25% WET, 25% WET").
    
    Transcription: {clean_transcription}
    """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(completion.choices[0].message.content)
    
    # 5. Nettoyage dynamique
    data["INFO"] = data.get("INFO", "").replace("INFORMATION", "").strip()
    data["RWY"] = "26 IN USE"
    data["RAW_TEXT"] = clean_transcription
    
    # Correction dynamique des contaminants (Whisper 2.5% -> 25%)
    if "CONTAM" in data:
        data["CONTAM"] = str(data["CONTAM"]).replace("2.5", "25").replace("PERCENT", "%")

    # Logique de visibilité automatique
    if "CAVOK" in clean_transcription.upper():
        data["RVR"] = "CAVOK"
    elif not data.get("RVR") or str(data.get("RVR")).upper() == "NONE":
        data["RVR"] = "N/A"

    # 6. Injection dans le template
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", str(value))
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(">>> SUCCÈS : Dashboard mis à jour.")

if __name__ == "__main__":
    run_atis_system()
