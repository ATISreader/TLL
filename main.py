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

    # 1. Transcription avec Whisper (Paramètres de patience maximale)
    print(">>> CHARGEMENT DU MODÈLE : medium...")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    
    print(">>> TRANSCRIPTION EN COURS...")
    # no_speech_threshold : évite de couper si la voix est faible
    # vad_filter=False : crucial pour ne pas que le souffle radio soit pris pour du silence
    # silence_size : attend 1 seconde de vrai silence avant de segmenter
    segments, _ = model.transcribe(
        audio_file, 
        beam_size=5, 
        condition_on_previous_text=False,
        vad_filter=False,
        no_speech_threshold=0.3,
        silence_size=1000
    )
    
    unique_segments = []
    seen = set()
    for segment in segments:
        text = segment.text.strip()
        # On ignore les segments vides ou trop courts (parasites)
        if text not in seen and len(text) > 3:
            unique_segments.append(text)
            seen.add(text)
            
    transcription = " ".join(unique_segments).upper()
    
    # 2. Application du dictionnaire
    for erreur, correction in replacement_dict.items():
        transcription = transcription.replace(erreur.upper(), correction.upper())
    
    # --- NETTOYAGE DES CHIFFRES & VIRGULES ---
    transcription = transcription.replace(",", "")
    transcription = re.sub(r'(?<= \d)\s+(?=\d)', '', transcription)
    
    # 3. Extraction du bloc (Cherche la dernière boucle pour maximiser les chances de complétude)
    start_marker = "THIS IS TALLINN"
    if start_marker in transcription:
        clean_transcription = transcription[transcription.rfind(start_marker):].strip()
    else:
        clean_transcription = transcription.strip()

    # 4. Analyse Groq
    print(">>> ANALYSE AVEC GROQ...")
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_KEY")
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are an aviation expert. Analyze this ATIS. Return ONLY a JSON object.
    Use "XXX" if a value is missing or unclear.
    - INFO: Letter only.
    - ZULU: HH:MM.
    - RWY: Identify the runway in use. It is usually "08 IN USE" or "26 IN USE".    
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
    
    # 5. Nettoyage et Sécurisation (Remplacement des None/Vides par XXX)
    data["RAW_TEXT"] = clean_transcription
    
    # Liste des clés à surveiller
    keys_to_check = ["INFO", "ZULU", "WIND", "RVR", "TEMP_DEWP", "QNH", "RCC", "CONTAM"]
    
    for key in keys_to_check:
        val = data.get(key)
        
        # Si la valeur est absente, nulle ou "None"
        if val is None or str(val).strip().upper() in ["NONE", "N/A", ""]:
            data[key] = "XXX"
            continue

        # Traitement spécifique pour le QNH (doit avoir 4 chiffres)
        if key == "QNH":
            digits = re.sub(r"\D", "", str(val))
            data[key] = f"{digits} HPA" if len(digits) == 4 else "XXX"
        
        # Formatage des listes/chaînes pour le HTML
        elif isinstance(val, list):
            data[key] = str(val[0]) if key == "WIND" else "<br>".join([str(x) for x in val])
        elif isinstance(val, str):
            data[key] = val.replace("[", "").replace("]", "").replace("'", "").replace('"', "").replace(",", "<br>")

    # 6. Injection dans le template
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    for key in data:
        html = html.replace("{{" + key + "}}", str(data[key]))
    
    # Nettoyage final au cas où des tags resteraient
    html = re.sub(r"\{\{.*?\}\}", "XXX", html)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f">>> SUCCÈS : Dashboard mis à jour.")

if __name__ == "__main__":
    run_atis_system()
