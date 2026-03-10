import os
import json
from groq import Groq
from faster_whisper import WhisperModel
import sys

def run_atis_system():
    print(">>> DÉMARRAGE DU SCRIPT")
    audio_file = "atis_recorded.wav"
    template_path = "template.html"
    index_path = "index.html"

    # Vérification taille fichier
    if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
        print(f">>> ERREUR: {audio_file} est vide ou absent !")
        sys.exit(1)

    # 1. Transcription locale
    print(">>> Transcription locale avec Whisper (tiny)...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_file)
    transcription = " ".join([segment.text for segment in segments])
    
    print(f">>> TEXTE TRANSCRIT : {transcription}")
    if not transcription.strip():
        print(">>> ERREUR: Whisper n'a rien transcrit !")
        sys.exit(1)

    # 2. Analyse Groq
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        print(">>> ERREUR: Clé GROQ_API_KEY manquante !")
        sys.exit(1)
        
    client = Groq(api_key=groq_api_key)
    prompt = f"""
    Tu es un expert ATIS. Analyse cette transcription et retourne UNIQUEMENT un JSON pur (sans texte autour).
    Transcription: {transcription}
    Clés requises: INFO, ZULU, RWY, QNH, WIND, RVR, TEMP_DEWP, RCC, CONTAM, RAW_TEXT
    """

    print(">>> Envoi à Groq...")
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    response_content = completion.choices[0].message.content
    print(f">>> RÉPONSE BRUTE GROQ : {response_content}")
    data = json.loads(response_content)
    
    # 3. Injection dans template
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", str(value))
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(">>> SUCCÈS : index.html généré.")

if __name__ == "__main__":
    run_atis_system()
