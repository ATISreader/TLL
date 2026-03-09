import os
import google.generativeai as genai
import json
import time

def run_atis_system():
    audio_file = "atis_recorded.wav"
    if not os.path.exists(audio_file): 
        print("Erreur: Fichier audio introuvable.")
        return

    # 1. Configuration de l'API Gemini
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    # Utilisation du modèle flash le plus récent
    model = genai.GenerativeModel("gemini-1.5-flash")

    # 2. Upload et attente du traitement
    print("Upload de l'audio...")
    audio_data = genai.upload_file(path=audio_file)
    
    # Petite boucle pour attendre que Google ait fini de traiter l'audio
    while audio_data.state.name == "PROCESSING":
        print("Traitement de l'audio par Google...")
        time.sleep(2)
        audio_data = genai.get_file(audio_data.name)

    if audio_data.state.name == "FAILED":
        print("Erreur de traitement audio chez Google.")
        return

    # 3. Prompt d'extraction
    prompt = """
    Tu es un expert en ATIS aéronautique. Analyse cet enregistrement ATIS.
    Réponds EXCLUSIVEMENT avec le format JSON suivant, sans texte avant ou après :
    {
        "INFO": "Lettre",
        "ZULU": "HH:MM",
        "RWY": "Numéro",
        "QNH": "Valeur",
        "WIND": "Dir/Force KT",
        "VIS": "Visibilité",
        "RVR": "Valeur ou ---",
        "TEMP_DEWP": "T / DP",
        "RCC": "Code",
        "CONTAM": "Type",
        "RAW_TEXT": "Transcription complète"
    }
    """

    print("Analyse par l'IA...")
    response = model.generate_content([prompt, audio_data])
    
    # 4. Parsing et Injection
    try:
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
    except Exception as e:
        print(f"Erreur de parsing : {e}")
        print(f"Réponse brute de l'IA : {response.text}")
        return

    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            html_content = f.read()
    
        for key, value in data.items():
            placeholder = "{{" + str(key) + "}}"
            html_content = html_content.replace(placeholder, str(value))
                
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            print("Dashboard mis à jour avec succès.")

if __name__ == "__main__":
    run_atis_system()
