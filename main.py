import os
import json
from groq import Groq
from faster_whisper import WhisperModel

def run_atis_system():
    print(">>> DÉMARRAGE DU SCRIPT")
    audio_file = "atis_recorded.wav"
    template_path = "template.html"
    index_path = "index.html"

    if not os.path.exists(audio_file):
        print(f">>> ERREUR: {audio_file} introuvable.")
        return

    # 1. Transcription locale (Gratuite & Illimitée)
    print(">>> Transcription locale avec Whisper...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_file)
    transcription = " ".join([segment.text for segment in segments])
    print(f">>> TRANSCRIPTION : {transcription}")

    # 2. Analyse JSON via Groq
    groq_api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=groq_api_key)

    prompt = f"""
    Analyse cette transcription ATIS et extrais les données en JSON pur.
    Transcription: {transcription}
    Retourne uniquement le JSON avec ces clés: 
    INFO, ZULU, RWY, QNH, WIND, RVR, TEMP_DEWP, RCC, CONTAM, RAW_TEXT
    """

    print(">>> Envoi à Groq (Llama 3.3)...")
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    data = json.loads(completion.choices[0].message.content)
    
    # 3. Mise à jour du template (identique)
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", str(value))
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(">>> SUCCÈS : Dashboard mis à jour.")

if __name__ == "__main__":
    run_atis_system()
