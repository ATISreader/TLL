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
    
    # Supprime les doubles espaces
    transcription = re.sub(r'\s+', ' ', transcription).strip()
    
    # Nettoyage des points dans les nombres (ex: 1.701 -> 1701)
    transcription = re.sub(r'(\d)\.(\d{2,3})', r'\1\2', transcription) 

    # --- COLLAGE DES CHIFFRES ---
    transcription = re.sub(r'(?<= \d)\s+(?=\d)', '', transcription)

    # 2. Application du dictionnaire (Corrections phonétiques)
    sorted_dict = dict(sorted(replacement_dict.items(), key=lambda x: len(x[0]), reverse=True))
    for erreur, correction in sorted_dict.items():
        transcription = transcription.replace(erreur.upper(), correction.upper())
    
    # 3. Extraction de la boucle complète avec marge pour l'heure
    start_marker = "THIS IS TALLINN"
    end_marker = "OUT"
    
    start_pos = transcription.find(start_marker)
    if start_pos != -1:
        # On recule de 30 caractères pour attraper l'heure qui précède souvent l'ID
        search_start = max(0, start_pos - 30)
        fragment = transcription[search_start:]
        
        end_pos = fragment.find(end_marker)
        if end_pos != -1:
            clean_transcription = fragment[:end_pos + len(end_marker)].strip()
        else:
            clean_transcription = fragment.strip()
    else:
        clean_transcription = transcription.strip()

    # 4. Analyse, Nettoyage et Standardisation par Groq
    print(">>> GROQ : RECONSTRUCTION DE LA BOUCLE ET EXTRACTION...")
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_KEY")
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are an expert Aviation AI. Reconstruct this ATIS loop professionally.
    
    CORE RULES:
    1. RECONSTRUCT: Create a single, clean paragraph.
       - YOU MUST INCLUDE THE MAIN TIME (e.g., "TIME 1701") at the start.
       - INCLUDE the Runway Condition Report time (e.g., "AT 1635").
       - START with the airport ID: "THIS IS TALLINN AIRPORT..."
       - END strictly with: "...INFORMATION [LETTER] OUT."
       - FIX phonetic errors (2.5% -> 25%, HECTOR PASCAL -> HPA).
       - FORMAT all numbers as clean digits (no dots in hours).
    
    2. EXTRACT data into a JSON object.
    
    Transcription to process: {clean_transcription}

    Return ONLY this JSON structure:
    {{
      "CLEAN_TEXT": "The full professional text with ALL times and data",
      "INFO": "Letter",
      "ZULU": "HH:MM",
      "RWY": "XX IN USE",
      "WIND": "DIR/SPD (GUSTS)",
      "RVR": "Visibility/CAVOK",
      "TEMP_DEWP": "T/D",
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
    
    # 5. Nettoyage et Sécurisation des données pour le HTML
    # On privilégie le texte propre de Groq pour la section Transcription
    data["RAW_TEXT"] = data.get("CLEAN_TEXT", clean_transcription)
    
    keys_to_check = ["INFO", "ZULU", "WIND", "RVR", "TEMP_DEWP", "QNH", "RCC", "CONTAM", "RWY"]
    
    for key in keys_to_check:
        val = data.get(key)
        
        if val is None or str(val).strip().upper() in ["NONE", "N/A", ""]:
            data[key] = "XXX"
            continue

        if key == "QNH":
            digits = re.sub(r"\D", "", str(val))
            data[key] = f"{digits} HPA" if len(digits) == 4 else "XXX"
        
        elif isinstance(val, list):
            data[key] = "<br>".join([str(x) for x in val])
        elif isinstance(val, str):
            data[key] = val.replace("[", "").replace("]", "").replace("'", "").replace('"', "")

    # 6. Injection dans le template HTML
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    for key in data:
        html = html.replace("{{" + key + "}}", str(data[key]))
    
    # Sécurité pour les tags non remplacés
    html = re.sub(r"\{\{.*?\}\}", "XXX", html)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f">>> SUCCÈS : Dashboard mis à jour avec Information {data.get('INFO', '?')}.")

if __name__ == "__main__":
    run_atis_system()
