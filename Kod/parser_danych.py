import os

def _parsuj_kat_hz(hz_str: str) -> tuple[int, int, int]:
    """
    Funkcja pomocnicza do ekstrakcji stopni, minut i sekund z tekstu.

    Parametry:
    ----------
    hz_str : str
        Kąt poziomy zapisany w formie tekstowej (np. "180°00'00"").

    Zwraca:
    -------
    tuple[int, int, int]
        Krotka zawierająca trzy wartości całkowite: (stopnie, minuty, sekundy).
    """
    czysty_tekst = hz_str.replace("°", " ").replace("'", " ").replace('"', ' ')
    czesci = czysty_tekst.split()
    
    if len(czesci) >= 3:
        return int(czesci[0]), int(czesci[1]), int(czesci[2])
    return 0, 0, 0

def wczytaj_i_parsuj_dziennik(sciezka_pliku: str) -> tuple[dict, dict]:
    """
    Wczytuje plik tekstowy dziennika pomiarowego i parsuje go na słowniki.

    Parametry:
    ----------
    sciezka_pliku : str
        Ścieżka systemowa do pliku tekstowego z danymi wejściowymi.

    Zwraca:
    -------
    tuple[dict, dict]
        Krotka dwóch słowników: 
        - metadane (dict): Informacje o stacji i instrumencie (klucz: wartość).
        - obserwacje (dict): Zmierzone parametry biegunowe (klucz: lista wartości).
    """
    metadane = {
        'stanowisko': None,
        'nawiazanie': None,
        'x0': None,
        'y0': None,
        'mHz_sec': None,
        'mD_mm': None,
        'mD_ppm': 0.0
    }
    
    obserwacje = {
        'pkt': [],
        'data': [],
        'hz_deg': [],
        'hz_min': [],
        'hz_sec': [],
        'hz_dd': [],
        'd_m': []
    }

    if not os.path.exists(sciezka_pliku):
        raise FileNotFoundError(f"Brak pliku wejściowego w lokalizacji: {sciezka_pliku}")
        
    w_sekcji_obserwacji = False
    
    with open(sciezka_pliku, 'r', encoding='utf-8') as plik:
        for linia in plik:
            linia = linia.strip()
            
            if not linia or linia.startswith("==") or linia.startswith("--"):
                continue
                
            if "OBSERWACJE" in linia:
                w_sekcji_obserwacji = True
                continue
                
            if not w_sekcji_obserwacji:
                
                if "Stanowisko" in linia:
                    #zamieniam nawiasy i przecinki na spacje, żeby .split() dał czystą listę wyrazów
                    czysta_linia = linia.replace("(", " ").replace(")", " ").replace(",", " ").replace(":", " ").replace("=", " = ")
                    wyrazy = czysta_linia.split()
                    
                    # nazwa stanowiska - słowo po stanowisko
                    for j in range(len(wyrazy)):
                        if wyrazy[j] == "Stanowisko" and j + 1 < len(wyrazy):
                            metadane['stanowisko'] = wyrazy[j+1]
                            
                    # współrzędne X0 i Y0
                    for j in range(len(wyrazy)):
                        if wyrazy[j].startswith("X") and j + 2 < len(wyrazy) and wyrazy[j+1] == "=":
                            metadane['x0'] = float(wyrazy[j+2])
                        if wyrazy[j].startswith("Y") and j + 2 < len(wyrazy) and wyrazy[j+1] == "=":
                            metadane['y0'] = float(wyrazy[j+2])
                            
                elif "Nawiązanie" in linia or "Nawiazanie" in linia:
                    # zamiana dwukropki na spacje by łatwiej było wyciągnąć ostatnie słowo
                    czysta_linia = linia.replace(":", " ")
                    wyrazy = czysta_linia.split()
                    metadane['nawiazanie'] = wyrazy[1]
                    
                elif "kątowa" in linia or "katowa" in linia:
                    # taka sama zamiana 
                    czysta_linia = linia.replace('"', ' ').replace("'", " ").replace(":", " ")
                    wyrazy = czysta_linia.split()
                    for w in wyrazy:
                        if w.isdigit():
                            metadane['mHz_sec'] = float(w)
                            
                elif "długości" in linia or "dlugosci" in linia:
                    # usunięcie jednostek i znaków by łatwiej było wyciągnąć liczby
                    czysta_linia = linia.replace("+", " ").replace(":", " ").replace(",", " ")
                    wyrazy = czysta_linia.split()
                    for j in range(len(wyrazy)):
                        if wyrazy[j] == "mm" and j > 0:
                            metadane['mD_mm'] = float(wyrazy[j-1])
                        elif wyrazy[j] == "ppm" and j > 0:
                            metadane['mD_ppm'] = float(wyrazy[j-1])
            else:
                if linia.startswith("Pkt") or "KONIEC" in linia:
                    continue

                czesci = linia.split()
                if len(czesci) >= 4:
                    nr_punktu = czesci[0]
                    data_pom = czesci[1]
                    hz_tekst = czesci[2]
                    dlugosc_tekst = czesci[3]
                    
                    try:
                        deg, pt_min, sec = _parsuj_kat_hz(hz_tekst)
                        hz_dd = deg + pt_min / 60.0 + sec / 3600.0
                        dlugosc_m = float(dlugosc_tekst)
                        
                        obserwacje['pkt'].append(nr_punktu)
                        obserwacje['data'].append(data_pom)
                        obserwacje['hz_deg'].append(deg)
                        obserwacje['hz_min'].append(pt_min)
                        obserwacje['hz_sec'].append(sec)
                        obserwacje['hz_dd'].append(hz_dd)
                        obserwacje['d_m'].append(dlugosc_m)
                    except ValueError:
                        continue
                        
    return metadane, obserwacje