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
    
    # 2. Application du dictionnaire (Nettoyage initial)
    for erreur, correction in replacement_dict.items():
        transcription = transcription.replace(erreur.upper(), correction.upper())
    
    # --- NETTOYAGE DES CHIFFRES ---
    # A. Supprime les virgules entre les chiffres (ex: 1, 0, 1, 0 -> 1 0 1 0)
    transcription = re.sub(r'(\d),\s*(\d)', r'\1 \2', transcription)
    # B. Colle les chiffres (ex: 1 0 1 0 -> 1010)
    transcription = re.sub(r'(?<=\d)\s+(?=\d)', '', transcription)
    
    # 3. Extraction du bloc unique (Version Robuste)
    start_marker = "THIS IS TALLINN"
    if start_marker in transcription:
        # On prend tout à partir du premier "THIS IS TALLINN" jusqu'à la fin de l'audio
        # pour être sûr de ne rien couper (vent, QNH, etc.)
        full_atis = transcription[transcription.find(start_marker):]
        
        # Si le message se répète (plusieurs boucles), on ne garde que la première
        parts = full_atis.split(start_marker)
        # parts[0] est vide, parts[1] est le premier message complet
        clean_transcription = start_marker + parts[1] if len(parts) > 1 else full_atis
    else:
        clean_transcription = transcription

    # 4. Analyse Groq
    print(">>> ANALYSE AVEC GROQ...")
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_KEY")
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are an aviation expert. Analyze this ATIS. Return ONLY a JSON object.
    - INFO: Letter only.
    - ZULU: HH:MM.
    - RWY: "26 IN USE".
    - WIND: Extract ONLY the touchdown zone wind (the first one mentioned).
    - RVR: Extract visibility or "CAVOK".
    - TEMP_DEWP: Format (e.g. 10, -4).
    - QNH: Extract ONLY the 4 digits.
    - RCC: Format X, X, X.
    - CONTAM: Extract state.
    
    Transcription: {clean_transcription}
    """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(completion.choices[0].message.content)
    
    # 5. Nettoyage dynamique des données pour le HTML
    data["INFO"] = data.get("INFO", "").replace("INFORMATION", "").strip()
    data["RAW_TEXT"] = clean_transcription
    
    # Sécurité QNH
    qnh_raw = str(data.get("QNH", "1011"))
    qnh_digits = re.sub(r"\D", "", qnh_raw)
    data["QNH"] = f"{qnh_digits} HPA" if qnh_digits else "1011 HPA"

    # Nettoyage des listes et formatage (Wind, RCC, etc.)
    for key in ["WIND", "CONTAM", "RCC", "RVR"]:
        val = data.get(key)
        if isinstance(val, list):
            # Pour le vent, on ne garde que le premier élément (TDZ)
            data[key] = str(val[0]) if key == "WIND" else "<br>".join([str(x) for x in val])
        elif isinstance(val, str):
            data[key] = val.replace("[", "").replace("]", "").replace("'", "").replace('"', "").replace(",", "<br>")

    # 6. Injection dans le template
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", str(value))
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f">>> SUCCÈS : Dashboard mis à jour avec Information {data.get('INFO')}.")

if __name__ == "__main__":
    run_atis_system()
