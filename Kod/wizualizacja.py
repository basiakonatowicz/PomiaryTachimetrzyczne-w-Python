import os
import matplotlib.pyplot as plt

def rysuj_szkic_sytuacyjny(metadane: dict, obliczone: dict, folder_wyjsciowy: str):
    """
    Generuje przestrzenny szkic sytuacyjny wyznaczonych współrzędnych (oś rzędnych i odciętych).
    Zaznacza wielobok, stanowisko oraz pomiary serii kontrolnej.

    Parametry:
    ----------
    metadane : dict
        Słownik z współrzędnymi stanowiska pomiarowego.
    obliczone : dict
        Słownik ze współrzędnymi wyznaczonych punktów.
    folder_wyjsciowy : str
        Katalog docelowy zapisu pliku.

    Zwraca:
    -------
    str
        Ścieżka do wygenerowanego pliku graficznego (.png).
    """

    plt.figure(figsize=(10, 10))
    
    x_wielo, y_wielo = [], []
    x_reg, y_reg = [], []
    
    for i in range(len(obliczone['pkt'])):
        nazwa = obliczone['pkt'][i]
        x = obliczone['x'][i]
        y = obliczone['y'][i]
        if "_" in nazwa:
            x_reg.append(y)  # zamiana osi geodezyjnych  
            y_reg.append(x)  
        else:
            x_wielo.append(y)
            y_wielo.append(x)
            plt.annotate(nazwa, (y, x), textcoords="offset points", xytext=(5,5), ha='center', fontsize=8)

    # główny wielobok 
    if len(x_wielo) > 0:
        plt.plot(x_wielo + [x_wielo[0]], y_wielo + [y_wielo[0]], color='steelblue', linestyle='-', linewidth=1.5, zorder=1)
        plt.scatter(x_wielo, y_wielo, c='darkblue', marker='o', label='Wielobok', zorder=2)
        
    # punkty serii 7_xx 
    if len(x_reg) > 0:
        plt.scatter(x_reg, y_reg, c='firebrick', marker='.', alpha=0.7, label='Seria 7_xx', zorder=2)

    # stanowisko (X0, Y0) i nawiązanie
    x0, y0 = metadane.get('x0'), metadane.get('y0')
    if x0 is not None and y0 is not None:
        plt.scatter([y0], [x0], c='brown', marker='*', s=150, label='Stanowisko O', zorder=3)
        plt.annotate('O', (y0, x0), textcoords="offset points", xytext=(5,5), fontsize=10, fontweight='bold', color='brown')
        
        # nawiązanie A - X_A = 1000.0, Y_A = 1200.0
        xa, ya = 1000.0, 1200.0
        plt.plot([y0, ya], [x0, xa], color='rosybrown', linestyle='-', linewidth=1.5, zorder=1)
        plt.scatter([ya], [xa], c='darkgreen', marker='^', s=100, label='Nawiązanie A', zorder=3)
        plt.annotate('A', (ya, xa), textcoords="offset points", xytext=(5,5), fontsize=10, fontweight='bold', color='darkgreen')

    plt.title('Lokalizacja punktów pomiarowych — wielobok + monitoring pkt 7\nStanowisko O | Nawiązanie A')
    plt.xlabel('Y [m]')  
    plt.ylabel('X [m]')  
    
    plt.grid(True, linestyle=':', alpha=0.6, color='lightgray')
    plt.axis('equal')  
    plt.legend(loc='lower left')
    
    sciezka = os.path.join(folder_wyjsciowy, "01_szkic_sytuacyjny.png")
    plt.savefig(sciezka, dpi=300, bbox_inches='tight')
    plt.close()
    return sciezka


def rysuj_wykres_bledow(obliczone: dict, folder_wyjsciowy: str):
    """
    Tworzy wykres słupkowy prezentujący wartości błędu położenia punktu (mP).
    Oblicza i nakłada na wykres linie trendu statystycznego (średnią, min, max).

    Parametry:
    ----------
    obliczone : dict
        Słownik zawierający wyliczone wartości błędów mp_mm.
    folder_wyjsciowy : str
        Katalog docelowy zapisu pliku.

    Zwraca:
    -------
    str
        Ścieżka do pliku graficznego (.png) lub None w przypadku braku danych.
    """
    # odrzuczenie wartości None 
    bledy_mp = [mp for mp in obliczone['mp_mm'] if mp is not None]
    nazwy_pkt = [obliczone['pkt'][i] for i, mp in enumerate(obliczone['mp_mm']) if mp is not None]
    
    if not bledy_mp:
        return None  
        
    min_mp = min(bledy_mp)
    max_mp = max(bledy_mp)
    srednia_mp = sum(bledy_mp) / len(bledy_mp)
    
    plt.figure(figsize=(12, 6))
    plt.bar(nazwy_pkt, bledy_mp, color='skyblue', edgecolor='black')
    
    # Linia
    plt.axhline(srednia_mp, color='red', linestyle='--', label=f'Średnia: {srednia_mp:.2f} mm')
    

    tekst_stat = f"Min: {min_mp:.2f} mm | Max: {max_mp:.2f} mm"
    plt.title(f'Wykres błędu położenia punktu mP\n({tekst_stat})')
    plt.xlabel('Numer punktu')
    plt.ylabel('Błąd mP [mm]')
    plt.xticks(rotation=90, fontsize=7)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.legend()
    
    sciezka = os.path.join(folder_wyjsciowy, "02_wykres_bledow.png")
    plt.tight_layout()
    plt.savefig(sciezka, dpi=300)
    plt.close()
    return sciezka


def rysuj_wykresy_regresji(wyniki_regresji: dict, folder_wyjsciowy: str):
    """
    Generuje dwupanelowy wykres (subplots) dla wyników modelu regresji.
    Lewy panel ukazuje chmurę punktów z linią trendu, prawy rozkład residuów wokół zera.

    Parametry:
    ----------
    wyniki_regresji : dict
        Słownik z parametrami modelu i wartościami estymowanymi.
    folder_wyjsciowy : str
        Katalog docelowy zapisu pliku.

    Zwraca:
    -------
    str
        Ścieżka do wygenerowanego pliku graficznego (.jpg / .png).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # pierwszy panel to prosta regresji
    x_val = wyniki_regresji['x']
    y_val = wyniki_regresji['y']
    a = wyniki_regresji['a']
    b = wyniki_regresji['b']
    
    ax1.scatter(x_val, y_val, color='blue', alpha=0.6, label='Punkty serii')
    
    x_min, x_max = min(x_val), max(x_val)
    y_min, y_max = a * x_min + b, a * x_max + b
    ax1.plot([x_min, x_max], [y_min, y_max], color='red', linewidth=2, label=f'Y = {a:.3f}*X + {b:.2f}')
    
    ax1.set_title(f"Regresja liniowa\n(R^2 = {wyniki_regresji['r2']:.4f})")
    ax1.set_xlabel('X [m]')
    ax1.set_ylabel('Y [m]')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # panel 2- wykres residuów
    nazwy = wyniki_regresji['nazwy']
    residua = wyniki_regresji['e']
    
    ax2.bar(nazwy, residua, color='orange', edgecolor='black')
    ax2.axhline(0, color='red', linestyle='-')
    
    ax2.set_title(f"Residua modelu (błędy dopasowania)\n(Błąd standardowy Se = {wyniki_regresji['se']:.3f} m)")
    ax2.set_xlabel('Pkt pomiarowy')
    ax2.set_ylabel('Wartość residuum e [m]')
    ax2.tick_params(axis='x', rotation=90, labelsize=7)
    ax2.grid(axis='y', linestyle='--', alpha=0.6)
    
    sciezka = os.path.join(folder_wyjsciowy, "03_wykresy_regresji.png")
    plt.tight_layout()
    plt.savefig(sciezka, dpi=300)
    plt.close()
    return sciezka