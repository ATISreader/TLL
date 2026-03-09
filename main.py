import os
from google import genai
import json
import time

def run_atis_system():
    audio_file = "atis_recorded.wav"
    if not os.path.exists(audio_file): 
        print("Erreur: Fichier audio introuvable.")
        return

    # 1. Initialisation du nouveau client GenAI
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # 2. Upload de l'audio
    print(f"Upload de {audio_file}...")
    try:
        # Sur le nouveau SDK, on upload directement dans l'appel ou via upload
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()

        # 3. Prompt et Analyse directe (Le nouveau SDK gère l'attente différemment)
        prompt = """
        Tu es un expert en ATIS aéronautique. Analyse cet audio ATIS.
        Réponds EXCLUSIVEMENT avec un objet JSON structuré comme ceci, sans texte autour :
        {
            "INFO": "Lettre",
            "ZULU": "Heure",
            "RWY": "Piste",
            "QNH": "Valeur",
            "WIND": "Vent",
            "VIS": "Visibilité",
            "RVR": "RVR ou ---",
            "TEMP_DEWP": "T/DP",
            "RCC": "RCC",
            "CONTAM": "Contaminants",
            "RAW_TEXT": "Transcription complète"
        }
        """

        print("Analyse par Gemini 2.0 Flash...")
        # Utilisation de la méthode native pour l'audio sur Gemini 2.0
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                prompt,
                {"mime_type": "audio/wav", "data": audio_bytes}
            ]
        )
        
        # Nettoyage de la réponse
        output = response.text.strip()
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
            
        data = json.loads(output)
        
    except Exception as e:
        print(f"Erreur avec le nouveau SDK : {e}")
        return

    # 4. Injection dans le template HTML
    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            html_content = f.read()
    
        for key, value in data.items():
            placeholder = "{{" + str(key) + "}}"
            html_content = html_content.replace(placeholder, str(value))
                
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            print("Dashboard mis à jour avec succès (SDK v2) !")

if __name__ == "__main__":
    run_atis_system()
