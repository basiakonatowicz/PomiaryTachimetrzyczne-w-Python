import os
from datetime import datetime

def generuj_raport_obliczen(metadane: dict, obliczone: dict, folder_wyjsciowy: str, zapisz_bledy: bool = True) -> str:
    """
    Generuje sformatowany raport tekstowy z wynikami obliczeń współrzędnych i pola powierzchni.
    Dynamicznie dostosowuje układ tabeli, decydując o dodaniu kolumn z błędami.

    Parametry:
    ----------
    metadane : dict
        Słownik z danymi nagłówkowymi (wykorzystywane do opisu stacji).
    obliczone : dict
        Słownik z wynikami obliczeń.
    folder_wyjsciowy : str
        Ścieżka do katalogu, w którym zostanie zapisany plik.
    zapisz_bledy : bool, domyślnie True
        Flaga decydująca o zapisie analizy dokładności. Jeśli False, błędy są pomijane.

    Zwraca:
    -------
    str
        Pełna ścieżka systemowa do nowo utworzonego pliku raportu (.txt).
    """
    nazwa_pliku = "raport_obliczen.txt"
    sciezka = os.path.join(folder_wyjsciowy, nazwa_pliku)
    
    analiza_dokladnosci = (obliczone['mx_mm'][0] is not None) and zapisz_bledy
    
    with open(sciezka, 'w', encoding='utf-8') as plik:
        # nagłówek raportu
        plik.write("="*85 + "\n")
        plik.write("RAPORT Z OBLICZEŃ WSPÓŁRZĘDNYCH I ANALIZY DOKŁADNOŚCI\n")
        plik.write("="*85 + "\n")
        plik.write(f"Data wygenerowania : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        plik.write(f"Stanowisko         : {metadane.get('stanowisko', 'Brak')} (X0 = {metadane.get('x0'):.3f} m, Y0 = {metadane.get('y0'):.3f} m)\n")
        plik.write(f"Nawiązanie         : {metadane.get('nawiazanie', 'Brak')}\n")
        plik.write("-" * 85 + "\n\n")
        
        # tabela wyników
        if analiza_dokladnosci:
            naglowek = f"{'Pkt':<6} | {'dX [m]':>9} | {'dY [m]':>9} | {'X [m]':>10} | {'Y [m]':>10} | {'mX [mm]':>7} | {'mY [mm]':>7} | {'mP [mm]':>7}"
        else:
            naglowek = f"{'Pkt':<6} | {'dX [m]':>9} | {'dY [m]':>9} | {'X [m]':>10} | {'Y [m]':>10}"
            
        plik.write(naglowek + "\n")
        plik.write("-" * len(naglowek) + "\n")
        
        # wiersze z danymi
        for i in range(len(obliczone['pkt'])):
            pkt = obliczone['pkt'][i]
            dx = obliczone['dx'][i]
            dy = obliczone['dy'][i]
            x = obliczone['x'][i]
            y = obliczone['y'][i]
            
            if analiza_dokladnosci:
                mx = obliczone['mx_mm'][i]
                my = obliczone['my_mm'][i]
                mp = obliczone['mp_mm'][i]
                plik.write(f"{pkt:<6} | {dx:>9.3f} | {dy:>9.3f} | {x:>10.3f} | {y:>10.3f} | {mx:>7.3f} | {my:>7.3f} | {mp:>7.3f}\n")
            else:
                plik.write(f"{pkt:<6} | {dx:>9.3f} | {dy:>9.3f} | {x:>10.3f} | {y:>10.3f}\n")
                
        # sekcja z polem powierzchni   (jeśli obliczona)
        if 'pole_gaussa' in obliczone:
            pole_m2, pole_ha, wierzcholki = obliczone['pole_gaussa']
            plik.write("\n" + "="*85 + "\n")
            plik.write("POLE POWIERZCHNI WIELOBOKU (metoda Gaussa)\n")
            plik.write("="*85 + "\n")
            plik.write(f"Liczba wierzcholkow: {wierzcholki}\n")
            plik.write(f"Pole powierzchni   : {pole_m2:.3f} m2\n")
            plik.write(f"                   : {pole_ha:.6f} ha\n")
            plik.write("="*85 + "\n")
            
    return sciezka
def generuj_raport_regresji(wyniki_regresji: dict, folder_wyjsciowy: str) -> str:
    """
    Generuje raport tekstowy z wynikami analizy regresji liniowej.
    Zapisuje podsumowanie modelu, miary dopasowania oraz tabelę residuów.

    Parametry:
    ----------
    wyniki_regresji : dict
        Słownik z parametrami modelu zwrócony przez moduł obliczeniowy.
    folder_wyjsciowy : str
        Ścieżka do katalogu docelowego.

    Zwraca:
    -------
    str
        Pełna ścieżka systemowa do utworzonego pliku raportu (.txt).
    """
    nazwa_pliku = "raport_regresji.txt"
    sciezka = os.path.join(folder_wyjsciowy, nazwa_pliku)
    
    with open(sciezka, 'w', encoding='utf-8') as plik:
        plik.write("========================================================\n")
        plik.write("RAPORT REGRESJI LINIOWEJ\n")
        plik.write("Model: Y = a * X + b\n")
        plik.write("========================================================\n")
        plik.write("seria 7_XX\n\n")
        
        plik.write("PARAMETRY PROSTEJ REGRESJI\n")
        plik.write("-" * 56 + "\n")
        plik.write(f"a (nachylenie)       : {wyniki_regresji['a']:+.8f}\n")
        plik.write(f"b (wyraz wolny)      : {wyniki_regresji['b']:+.4f}\n")
        plik.write(f"Liczba punktow       : {wyniki_regresji['n']}\n\n")
        
        plik.write("STATYSTYKI DOPASOWANIA\n")
        plik.write("-" * 56 + "\n")
        plik.write(f"R^2 (wsp. determinacji) : {wyniki_regresji['r2']:.6f}\n")
        plik.write(f"Se (bl. std. residuow)  : {wyniki_regresji['se']:.6f} m\n\n")
        
        plik.write("RESIDUA e_i = Y_i - (a * X_i + b)\n")
        plik.write("-" * 56 + "\n")
        plik.write(f"{'Pkt':<6} | {'X [m]':>10} | {'Y [m]':>10} | {'Y_est [m]':>10} | {'e [m]':>9}\n")
        plik.write("-" * 56 + "\n")
        
        suma_e = 0.0
        for i in range(wyniki_regresji['n']):
            pkt = wyniki_regresji['nazwy'][i]
            x = wyniki_regresji['x'][i]
            y = wyniki_regresji['y'][i]
            y_est = wyniki_regresji['y_est'][i]
            e = wyniki_regresji['e'][i]
            suma_e += e
            
            plik.write(f"{pkt:<6} | {x:>10.4f} | {y:>10.4f} | {y_est:>10.4f} | {e:>9.4f}\n")
            
        plik.write("-" * 56 + "\n")
        plik.write(f"{'Suma e (kontrola):':<42} {suma_e:>+9.4f}\n")
        
    return sciezka