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

    # --- AJOUT ICI : COLLAGE DES CHIFFRES ---
    # Cette regex cherche un espace situé ENTRE deux chiffres et le supprime
    # Exemple : "1 0 5 0" -> "1050" | "RUNWAY 2 6" -> "RUNWAY 26"
    transcription = re.sub(r'(?<=\d)\s+(?=\d)', '', transcription)
    
    # 3. Extraction du bloc unique (plus robuste)
    # On cherche à capturer depuis "THIS IS TALLINN" jusqu'à "OUT" 
    # ou jusqu'à la prochaine répétition, ou simplement la fin du texte.
    pattern = r"(THIS IS TALLINN.*?)(?=THIS IS TALLINN|INFORMATION [A-Z] OUT|$)"
    match = re.search(pattern, transcription, re.IGNORECASE | re.DOTALL)
    
    if match:
        clean_transcription = match.group(1).strip()
    else:
        # Si on ne trouve pas le début standard, on nettoie au moins les répétitions
        clean_transcription = transcription.strip()

    # Sécurité anti-doublon interne : si le texte est encore trop long (répétition non captée)
    if len(clean_transcription) > 1000: # Un ATIS fait rarement plus de 800-900 caractères
        parts = clean_transcription.split("THIS IS TALLINN")
        if len(parts) > 2:
            clean_transcription = "THIS IS TALLINN" + parts[1]

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
    
    # --- SECURITÉ QNH ---
    # On cherche le QNH dans tout le JSON si la clé "QNH" est absente ou mal nommée
    qnh_final = "9999 HPA" # Valeur par défaut si tout échoue
    for k, v in data.items():
        if "QNH" in k.upper():
            digits = re.sub(r"\D", "", str(v))
            if len(digits) >= 4:
                qnh_final = f"{digits[:4]} HPA"
                break
    data["QNH"] = qnh_final

    # --- NETTOYAGE DES LISTES (WIND, CONTAM, RCC, RVR) ---
    # On ajoute explicitement RVR et Visibility pour éviter les ['...']
    keys_to_clean = ["WIND", "CONTAM", "RCC", "RVR", "VISIBILITY"]
    for key in keys_to_clean:
        # On essaie de trouver la clé même si elle est mal nommée par l'IA
        actual_key = next((k for k in data.keys() if k.upper() == key), key)
        val = data.get(actual_key)
        
        if isinstance(val, list):
            data[key] = "<br>".join([str(x) for x in val])
        elif isinstance(val, str):
            clean_val = val.replace("[", "").replace("]", "").replace("'", "").replace('"', "").replace(",", "<br>")
            data[key] = clean_val

    # Si l'IA a utilisé "VISIBILITY" au lieu de "RVR", on bascule la donnée
    if "VISIBILITY" in data and ("RVR" not in data or data["RVR"] == "N/A"):
        data["RVR"] = data["VISIBILITY"]

    # Correction contaminants spécifique (erreur Whisper 2.5% -> 25%)
    if "CONTAM" in data:
        data["CONTAM"] = str(data["CONTAM"]).replace("2.5", "25").replace("PERCENT", "%")

    # Logique de visibilité automatique (CAVOK)
    if "CAVOK" in clean_transcription.upper():
        data["RVR"] = "CAVOK"
    elif not data.get("RVR") or str(data.get("RVR")).upper() in ["NONE", "N/A", ""]:
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
