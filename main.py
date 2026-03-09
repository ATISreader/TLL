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
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Erreur: GEMINI_API_KEY non trouvée dans l'environnement.")
        return
        
    genai.configure(api_key=api_key)
    
    # Utilisation du nom de modèle complet pour éviter l'erreur 404
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    # 2. Upload et attente du traitement
    print(f"Upload de {audio_file}...")
    try:
        audio_data = genai.upload_file(path=audio_file)
        
        # Attente que le fichier soit prêt sur les serveurs Google
        while audio_data.state.name == "PROCESSING":
            print("Google traite l'audio...")
            time.sleep(3)
            audio_data = genai.get_file(audio_data.name)

        if audio_data.state.name == "FAILED":
            print("Échec du traitement audio par Google.")
            return
    except Exception as e:
        print(f"Erreur lors de l'upload : {e}")
        return

    # 3. Prompt d'extraction
    prompt = """
    Analyse cet audio ATIS aéronautique.
    Réponds EXCLUSIVEMENT avec un objet JSON structuré comme ceci :
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

    print("Analyse par Gemini...")
    try:
        response = model.generate_content([prompt, audio_data])
        
        # Nettoyage de la réponse
        output = response.text.strip()
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
            
        data = json.loads(output)
    except Exception as e:
        print(f"Erreur lors de l'analyse ou du parsing : {e}")
        print(f"Réponse brute reçue : {response.text if 'response' in locals() else 'Aucune'}")
        return

    # 4. Injection dans le template
    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            html_content = f.read()
    
        for key, value in data.items():
            placeholder = "{{" + str(key) + "}}"
            html_content = html_content.replace(placeholder, str(value))
                
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            print("Dashboard mis à jour avec succès !")

if __name__ == "__main__":
    run_atis_system()
