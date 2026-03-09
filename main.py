import os
from google import genai
from google.genai import types
import json

def run_atis_system():
    print(">>> DÉMARRAGE DU SCRIPT")
    audio_file = "atis_recorded.wav"
    template_path = "template.html"
    index_path = "index.html"

    if not os.path.exists(audio_file):
        print(f">>> ERREUR: Fichier {audio_file} INTROUVABLE sur le disque.")
        return

    # Configuration du client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(">>> ERREUR: GEMINI_API_KEY non configurée !")
        return
        
    client = genai.Client(api_key=api_key)
    
    try:
        print(f">>> Lecture de {audio_file}...")
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()

        prompt = """
        Analyse cet audio ATIS aéronautique. Réponds UNIQUEMENT avec un JSON pur (sans markdown).
        {
            "INFO": "Lettre", "ZULU": "Heure", "RWY": "Piste", "QNH": "Valeur",
            "WIND": "Vent", "RVR": "Visibilité/RVR", "TEMP_DEWP": "T/DP",
            "RCC": "RCC", "CONTAM": "Contaminants", "RAW_TEXT": "Transcription complète"
        }
        """

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")

        print(">>> Envoi à Gemini 2.0 Flash...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, audio_part]
        )
        
        output = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(output)
        print(f">>> DONNÉES PARSÉES : {data}")

        # Lecture du template
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    
        # Remplacement
        for key, value in data.items():
            html = html.replace("{{" + key + "}}", str(value))
        
        # Écriture forcée
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f">>> SUCCÈS : {index_path} a été écrit.")

    except Exception as e:
        print(f">>> ERREUR CRITIQUE : {e}")

if __name__ == "__main__":
    run_atis_system()
