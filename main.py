import os
from google import genai
from google.genai import types
import json

def run_atis_system():
    audio_file = "atis_recorded.wav"
    template_path = "template.html"
    index_path = "index.html"

    if not os.path.exists(audio_file): 
        print(f"❌ Erreur: {audio_file} introuvable.")
        return

    # 1. Initialisation du client
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    try:
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()

        prompt = """
        Analyse cet audio ATIS. Réponds EXCLUSIVEMENT avec ce JSON :
        {
            "INFO": "Lettre", "ZULU": "Heure", "RWY": "Piste", "QNH": "Valeur",
            "WIND": "Vent", "RVR": "Visibilité/RVR", "TEMP_DEWP": "T/DP",
            "RCC": "RCC", "CONTAM": "Contaminants", "RAW_TEXT": "Transcription"
        }
        """

        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")

        print("📡 Analyse Gemini en cours...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, audio_part]
        )
        
        # Nettoyage et parsing
        output = response.text.strip()
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
            
        data = json.loads(output)
        print(f"✅ Données reçues : {data['INFO']} à {data['ZULU']}Z")

        # 2. Injection dans le template
        if not os.path.exists(template_path):
            print(f"❌ Erreur: {template_path} introuvable.")
            return

        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    
        # Remplacement des balises
        for key, value in data.items():
            placeholder = "{{" + str(key) + "}}"
            html_content = html_content.replace(placeholder, str(value))
                
        # 3. Écriture forcée de l'index.html
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"🚀 Fichier {index_path} généré avec succès.")

    except Exception as e:
        print(f"💥 Erreur critique : {e}")

if __name__ == "__main__":
    run_atis_system()
