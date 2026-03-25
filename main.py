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

    # 1. Transcription avec Whisper
    print(">>> CHARGEMENT DU MODÈLE : medium...")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    
    print(">>> TRANSCRIPTION EN COURS...")
    segments, _ = model.transcribe(
        audio_file, 
        beam_size=5, 
        condition_on_previous_text=False,
        vad_filter=False,
        patience=2.0
    )
    
    unique_segments = []
    seen = set()
    for segment in segments:
        text = segment.text.strip()
        if text not in seen and len(text) > 3:
            unique_segments.append(text)
            seen.add(text)
            
    transcription = " ".join(unique_segments).upper()
    
    # --- PRÉ-NETTOYAGE ---
    transcription = transcription.replace("-", " ").replace(",", " ")
    
    # Supprime les doubles espaces (crucial pour le dictionnaire)
    transcription = re.sub(r'\s+', ' ', transcription).strip()
    
    # Dans ton script main.py, avant l'analyse Groq :
    transcription = re.sub(r'(\d)\.(\d{2,3})', r'\1\2', transcription) 
    # Transforme 1.701 en 1701

    # --- COLLAGE DES CHIFFRES ---
    transcription = re.sub(r'(?<= \d)\s+(?=\d)', '', transcription)

    # 2. Application du dictionnaire
    sorted_dict = dict(sorted(replacement_dict.items(), key=lambda x: len(x[0]), reverse=True))
    for erreur, correction in sorted_dict.items():
        transcription = transcription.replace(erreur.upper(), correction.upper())
    
    # 3. Extraction de la boucle complète (Début -> OUT)
    # On cherche le début standard d'un ATIS
    start_marker = "THIS IS TALLINN"
    end_marker = "OUT"
    
    start_index = transcription.find(start_marker)
    if start_index != -1:
        # On part du début trouvé
        fragment = transcription[start_index:]
        end_index = fragment.find(end_marker)
        if end_index != -1:
            # On coupe juste après le premier "OUT" trouvé
            clean_transcription = fragment[:end_index + len(end_marker)].strip()
        else:
            clean_transcription = fragment.strip()
    else:
        clean_transcription = transcription.strip()

    # 4. Analyse, Nettoyage et Standardisation par Groq
    print(">>> GROQ : RECONSTRUCTION DE LA BOUCLE ATIS...")
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_KEY")
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are an expert Aviation AI. I will provide a messy ATIS transcription loop.
    
    MISSION:
    1. RECONSTRUCT the loop into a single, professional, standardized ATIS paragraph.
       - START with: "THIS IS TALLINN AIRPORT..."
       - END with: "...INFORMATION [LETTER] OUT."
       - FIX phonetic errors (e.g., "HECTOR PASCAL" -> "HPA", "2.5%" -> "25%", "PATTY" -> "TOUCHDOWN").
       - FORMAT numbers as digits (e.g., "ONE SEVEN ZERO ONE" -> "1701").
    
    2. EXTRACT data into a JSON object.
    
    Transcription to process: {clean_transcription}

    Return ONLY this JSON structure:
    {{
      "CLEAN_TEXT": "The professional reconstructed text",
      "INFO": "Letter only",
      "ZULU": "HH:MM",
      "RWY": "XX IN USE",
      "WIND": "DIR/SPD (GUSTS)",
      "RVR": "Visibility/CAVOK",
      "TEMP_DEWP": "T/D (e.g. 13/02)",
      "QNH": "4 digits",
      "RCC": "X/X/X",
      "CONTAM": "State"
    }}
    """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(completion.choices[0].message.content)
    
    # 5. Nettoyage et Sécurisation
    # On utilise CLEAN_TEXT s'il existe, sinon on garde la transcription initiale
    data["RAW_TEXT"] = data.get("CLEAN_TEXT", clean_transcription)
    
    keys_to_check = ["INFO", "ZULU", "WIND", "RVR", "TEMP_DEWP", "QNH", "RCC", "CONTAM", "RWY"]
    
    for key in keys_to_check:
        val = data.get(key)
        
        if val is None or str(val).strip().upper() in ["NONE", "N/A", ""]:
            data[key] = "XXX"
            continue

        if key == "QNH":
            # On s'assure d'extraire les 4 chiffres si Groq a renvoyé "0990 HPA"
            digits = re.sub(r"\D", "", str(val))
            data[key] = f"{digits} HPA" if len(digits) == 4 else "XXX"
        
        elif isinstance(val, list):
            data[key] = "<br>".join([str(x) for x in val])
        elif isinstance(val, str):
            # On nettoie les caractères résiduels de formatage JSON
            data[key] = val.replace("[", "").replace("]", "").replace("'", "").replace('"', "") 

    # 6. Injection dans le template
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    for key in data:
        html = html.replace("{{" + key + "}}", str(data[key]))
    
    html = re.sub(r"\{\{.*?\}\}", "XXX", html)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f">>> SUCCÈS : Dashboard mis à jour.")

if __name__ == "__main__":
    run_atis_system()
