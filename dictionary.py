replacement_dict = {
    # --- Identification & Temps ---
    "INFLATION": "INFORMATION",
    "INFORMAATION": "INFORMATION",
    "DARWIN AIRPORT": "TALLINN AIRPORT",
    "DARLING AIRPORT": "TALLINN AIRPORT",
    "BUSINESS TALENT": "THIS IS TALLINN",
    "BUSINESS": "THIS IS",
    "STARLIN": "TALLINN",
    "TELLING": "TALLINN",
    "STALIN": "TALLINN",
    "TALIN": "TALLINN",
    "VST AIRPORT": "TALLINN AIRPORT",
    "SAILING":"TALLINN",
    "1450M": "1450", 
    "NO-SICK": "NOSIG",
    "STATUS SKY": "STATE OF SKY",
    "ITALIAN AIRPORT": "TALLINN AIRPORT",
    "LIMA OUT": "LIMA",
    "ONE SIX TWO ZERO": "1620",
    "TWO SIX ZERO DEGREES": "260 DEGREES",
    "ONE TWO KNOTS": "12 KNOTS",
    "ONE ZERO KILOMETERS": "10KM",
    "ONE ZERO ONE EIGHT": "1018",
    "WEHRFURT": "THE AIRPORT",
    "PATTY DOWN": "TOUCHDOWN",      # Correction de Whisper
    "PATTY": "TOUCHDOWN",           # Sécurité supplémentaire
    "2.5 PERCENT": "25 PERCENT",    # Correction mathématique pour les contaminants
    "TOUCH GROUND": "TOUCHDOWN",    # Correction terminologique
    "COVER OK": "CAVOK",            # Correction phonétique majeure
    "TRANSITION LEVEL 6.5": "TRANSITION LEVEL 65",
    "Z1": "ZONE",
    "TOUCH DOWN": "TOUCHDOWN",
    "WESTERN ITO": "THE VICINITY OF THE",
    "WESTERN ITALY": "THE VICINITY OF THE", # On l'a vu dans ton log précédent !
    "IN THE VICINITY": "IN THE VICINITY OF THE",
    "VICINITY OF AIRPORT": "VICINITY OF THE AIRPORT",
    "CAVOKAY": "CAVOK",
    "THIS IS TALENT": "THIS IS TALLINN",
    "THIS IS TELLIN": "THIS IS TALLINN",
    "WHICH IS TALLINN": "THIS IS TALLINN",

    # --- Piste & RCC ---
    "PATCH DOWN": "TOUCHDOWN",
    "PACHYDOWN": "TOUCHDOWN",
    "MEET POINT": "MIDPOINT",
    "SSTOP": "STOP",
    "STOPEND": "STOP END",
    "STOP-END": "STOP END",
    "TOP-END": "STOP END",
    "TOP END": "STOP END",
    "PATRICK IN USE": "RUNWAY 26 IN USE",
    "IN YOUTH": "IN USE",
    "MINUS 0 TO AN INCH": "MINUS 1",
    "KARAOKE": "CAVOK",

    # --- Météo & LVP ---
    "CAPITAL K": "CAVOK",
    "CABO K": "CAVOK",
    "DEW POINT": "DEWPOINT",
    "VIEW POINT": "DEWPOINT",
    "ESTHER PASCAL": "HPA",
    "EXTRA PASCAL": "HPA",
    "HECTOPASCAL": "HPA",
    "QNH 1010P": "QNH 1010",
    "LOWERCAST": "OVERCAST",
    "LOW VISIBILITY PROCEDURES": "LVP ACTIVE",
    "LVP ACTIVE IN OPERATION": "LVP ACTIVE",
    "NO-THICK": "NOSIG",
    "NO SEAT": "NOSIG",
    "TOUCH-TONE": "TOUCHDOWN",
    "CROSS-TREND": "CROSSWIND",
    "CLIMB": "TIME",
    "CAVALCADE": "CAVOK",
    "NO SEEK": "NOSIG",
    "EXTRA PASTEL": "HPA",
    "EXTRA PASCAL": "HPA",
    " 1, 0, 1, 0": " 1010", # Aide à coller les chiffres

    # --- Chiffres & Alphabet ---
    "ZERO": "0", "ONE": "1", "TWO": "2", "THREE": "3", "FOUR": "4",
    "FIVE": "5", "SIX": "6", "SEVEN": "7", "EIGHT": "8", "NINE": "9",
    "FREE": "3", # Whisper entend "Free" au lieu de "Three"
    "NINER": "9",
    "GULF": "G", "HOTEL": "H", "DELTA": "D", "VICTOR": "V",
    "KKNOTS": "KNOTS"
}
