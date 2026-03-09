import os
import google.generativeai as genai
import json

def run_atis_system():
    audio_file = "atis_recorded.wav"
    if not os.path.exists(audio_file): 
        print("Erreur: Fichier audio introuvable.")
        return

    # 1. Configuration de l'API Gemini
    # Assure-toi que GEMINI_API_KEY est bien configuré dans tes secrets GitHub
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")

    # 2. Upload et analyse de l'audio
    print("Analyse de l'audio en cours...")
    audio_data = genai.upload_file(path=audio_file)

    # Prompt ultra-précis pour l'aviation
    prompt = """
    Tu es un expert en ATIS aéronautique. Analyse cet enregistrement ATIS (EETN Tallinn).
    1. Donne une transcription textuelle complète et propre.
    2. Extrais les données structurées en format JSON.
    
    Réponds EXCLUSIVEMENT avec le format JSON suivant :
    {
        "INFO": "Lettre unique",
        "ZULU": "HH:MM",
        "RWY": "Numéro de piste",
        "QNH": "Valeur numérique",
        "WIND": "Direction/Force KT",
        "VIS": "Visibilité",
        "RVR": "Valeur ou ---",
        "TEMP_DEWP": "T / DP",
        "RCC": "Code RCC",
        "CONTAM": "Type de contaminant",
        "RAW_TEXT": "Transcription complète ici"
    }
    """

    response = model.generate_content([prompt, audio_data])
    
    # 3. Parsing de la réponse
    try:
        # On enlève les balises ```json si Gemini en ajoute
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
    except Exception as e:
        print(f"Erreur de lecture de l'IA : {e}")
        return

    # 4. Injection dans le template HTML
    template_path = "template.html"
    index_path = "index.html"

    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    
        # Remplacement dynamique des variables {{VARIABLE}}
        for key, value in data.items():
            placeholder = "{{" + str(key) + "}}"
            html_content = html_content.replace(placeholder, str(value))
                
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            print(f"Dashboard mis à jour avec succès pour l'information {data.get('INFO')}")

if __name__ == "__main__":
    run_atis_system()
