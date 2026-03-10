import os
import json
import sys
from groq import Groq
from faster_whisper import WhisperModel
# On importe votre dictionnaire externe
from dictionary import replacement_dict

def run_atis_system():
    print(">>> DÉMARRAGE DU SCRIPT")
    audio_file = "atis_recorded.wav"
    template_path = "template.html"
    index_path = "index.html"

    if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
        print(">>> ERREUR: Fichier audio manquant ou vide.")
        sys.exit(1)

    # 1. Transcription avec modèle SMALL
    print(">>> Transcription Whisper (small)...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_file)
    transcription = " ".join([segment.text for segment in segments])
    
    # 2. Nettoyage avec votre dictionnaire
    for erreur, correction in replacement_dict.items():
        transcription = transcription.replace(erreur, correction)
    
    print(f">>> TRANSCRIPTION NETTOYÉE : {transcription}")

    # 3. Analyse Groq
    groq_api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=groq_api_key)

    prompt = f"""
    Analyse cette transcription ATIS et retourne UNIQUEMENT un JSON pur.
    NE RETOURNE PAS d'objets imbriqués ou de listes, utilise uniquement des textes simples pour chaque clé.
    
    Transcription: {transcription}
    
    Clés attendues (valeurs en texte simple uniquement):
    - INFO: Lettre de l'information (ex: A, B, C)
    - ZULU: Heure de l'info (format HHMM)
    - RWY: Piste et état (ex: 26, humide)
    - QNH: Valeur QNH (ex: 1015 hPa)
    - WIND: Vent (ex: 220/11kt)
    - RVR: Visibilité (ex: 10km ou CAVOK)
    - TEMP_DEWP: Temp/Dewp (ex: 10/0)
    - RCC: Code RCC (ex: 5/5/5)
    - CONTAM: Contaminants (ex: Humide)
    - RAW_TEXT: La transcription originale
    """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(completion.choices[0].message.content)
    print(f">>> DONNÉES PARSÉES : {data}")
    
    # 4. Génération HTML
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", str(value))
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(">>> SUCCÈS : index.html mis à jour.")

if __name__ == "__main__":
    run_atis_system()
