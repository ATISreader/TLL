import os
from google import genai
from google.genai import types  # Import des types pour la validation
import json
import base64

def run_atis_system():
    audio_file = "atis_recorded.wav"
    if not os.path.exists(audio_file): 
        print("Erreur: Fichier audio introuvable.")
        return

    # 1. Initialisation du client
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    print(f"Lecture et encodage de {audio_file}...")
    try:
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()

        # 2. Construction du contenu avec les types officiels
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

        # Création de la partie audio selon les specs du nouveau SDK
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type="audio/wav"
        )

        print("Analyse par Gemini 2.0 Flash...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, audio_part]
        )
        
        # 3. Parsing de la réponse
        output = response.text.strip()
        # Sécurité pour extraire le JSON si l'IA ajoute des balises markdown
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
            
        data = json.loads(output)
        
    except Exception as e:
        print(f"Erreur lors de l'exécution : {e}")
        # Affiche la réponse brute en cas d'erreur de parsing pour débugger
        if 'response' in locals():
            print(f"Réponse brute : {response.text}")
        return

    # 4. Injection dans le template HTML
    template_path = "template.html"
    index_path = "index.html"

    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    
        for key, value in data.items():
            placeholder = "{{" + str(key) + "}}"
            html_content = html_content.replace(placeholder, str(value))
                
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            print(f"Succès ! Dashboard mis à jour (Information {data.get('INFO')})")

if __name__ == "__main__":
    run_atis_system()
