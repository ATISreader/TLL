import os
import re
from faster_whisper import WhisperModel
from dictionary import replacement_dict

def run_atis_system():
    audio_file = "atis_recorded.wav"
    if not os.path.exists(audio_file): 
        print("Erreur: Fichier audio introuvable.")
        return

    # 1. Transcription et Nettoyage
    # Utilisation du modèle 'medium.en' pour une meilleure précision sur les termes aéronautiques
    model = WhisperModel("medium.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_file, beam_size=5)
    full_text = " ".join([s.text for s in segments]).upper()

    # Application du dictionnaire de remplacement pour corriger Whisper
    for wrong, right in replacement_dict.items():
        full_text = re.sub(rf'\b{wrong}\b', right, full_text)

    # Nettoyage des itérations (on garde la version après "TALLINN AIRPORT")
    if "TALLINN AIRPORT" in full_text:
        parts = full_text.split("TALLINN AIRPORT")
        text = "TALLINN AIRPORT" + parts[-1]
    else:
        text = full_text

    # On ne garde qu'une seule mention d'INFORMATION pour éviter les doublons de lettre
    if text.count("INFORMATION") > 1:
        parts = text.split("INFORMATION")
        text = "INFORMATION " + parts[1]

    # 2. Fonction d'extraction sécurisée
    def find(pattern, src):
        res = re.findall(pattern, src, re.DOTALL)
        return res[-1] if res else "---"

    # 3. EXTRACTION DES DONNÉES
    info_val = find(r"INFORMATION\s+([A-Z])", text)
    rwy_val = find(r"RUNWAY\s+(\d{2})", text)
    qnh_val = find(r"QNH\s+(\d{4})", text)
    
    time_raw = find(r"TIME\s+(\d{4})", text)
    zulu_val = f"{time_raw[:2]}:{time_raw[2:]}" if time_raw != "---" else "---"

    # Vent (TDZ)
    w_dir = find(r"WIND.*?TOUCHDOWN ZONE,\s+(\d{3})", text)
    w_spd = find(r"WIND.*?TOUCHDOWN ZONE,.*?(\d+)\s+KNOTS", text)
    wind_display = f"{w_dir}°/{w_spd}KT" if w_dir != "---" else "---"

    # Visibilité et RVR
    vis_raw = find(r"VISIBILITY.*?TOUCHDOWN ZONE,\s+(\d+\s*\w+)", text)
    vis_display = vis_raw if vis_raw != "---" else ("CAVOK" if "CAVOK" in text else "---")
    
    rvr_raw = find(r"VISUAL RANGE.*?TOUCHDOWN ZONE,\s+(\d+)", text)
    rvr_display = f"RVR {rvr_raw}m" if rvr_raw != "---" else ""

    # Temp/Dewp
    t_val = find(r"TEMPERATURE\s+(\d+)", text)
    d_val = find(r"DEWPOINT\s+(\d+)", text)
    temp_dewp_display = f"{t_val}° / {d_val}°"

    # Variables de statut (RCC & Contaminants)
    rcc_val = "5/5/5" if "TOUCHDOWN 5" in text else "---"
    contam_val = "WET / WET / WET" if "WET" in text else "---"

    # 4. Dictionnaire de données pour le template
    data = {
        "INFO": info_val,
        "ZULU": zulu_val,
        "RWY": rwy_val,
        "QNH": qnh_val,
        "WIND": wind_display,
        "VIS": vis_display,
        "RVR": rvr_display,
        "TEMP_DEWP": temp_dewp_display,
        "RCC": rcc_val,
        "CONTAM": contam_val,
        "RAW_TEXT": text
    }

    # 5. Injection dans le template et génération de l'index.html
    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            html_content = f.read()
    
        for key, value in data.items():
            placeholder = "{{" + str(key) + "}}"
            html_content = html_content.replace(placeholder, str(value))
                
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            print("Dashboard mis à jour avec succès (index.html)")

if __name__ == "__main__":
    run_atis_system()
