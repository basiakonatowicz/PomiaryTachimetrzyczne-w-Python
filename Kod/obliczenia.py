import math
import numpy as np


def oblicz_wspolrzedne_i_bledy(metadane: dict, obserwacje: dict) -> dict:
    """
    Oblicza współrzędne płaskie X, Y oraz błędy pomiaru punktów na podstawie danych biegunowych.
    Wykorzystuje prawo propagacji błędów Gaussa. W przypadku braku danych o dokładności 
    instrumentu, obliczenia błędów są pomijane (wstawiana jest wartość None).

    Parametry:
    ----------
    metadane : dict
        Słownik z informacjami z nagłówka (x0, y0, mHz_sec, mD_mm, mD_ppm).
    obserwacje : dict
        Słownik ze sparsowanymi obserwacjami (d_m, hz_dd, pkt, data itp.).

    Zwraca:
    -------
    dict
        Słownik zawierający oryginalne obserwacje oraz listy nowych wartości: 
        dx, dy, x, y, mx_mm, my_mm, mp_mm.
    """
    x0 = metadane['x0']
    y0 = metadane['y0']
    mHz_sekundy = metadane['mHz_sec']
    mD_mm = metadane['mD_mm']
    mD_ppm = metadane['mD_ppm']
    
    wyniki = {
        'pkt': list(obserwacje['pkt']),
        'data': list(obserwacje['data']),
        'hz_dd': list(obserwacje['hz_dd']),
        'd_m': list(obserwacje['d_m']),
        'dx': [],
        'dy': [],
        'x': [],
        'y': [],
        'mx_mm': [],
        'my_mm': [],
        'mp_mm': []
    }
    
    analiza_dokladnosci = (mHz_sekundy is not None) and (mD_mm is not None)

    if analiza_dokladnosci:
        mHz_rad = mHz_sekundy * math.pi / (180.0 * 3600.0)
    
    for i in range(len(obserwacje['pkt'])):
        hz_deg = obserwacje['hz_dd'][i]
        d = obserwacje['d_m'][i]
        
        # Kąt  w radianach -> na potrzeby   math
        alpha_rad = math.radians(90.0 - hz_deg)
        
        # przyrosty
        dx = d * math.cos(alpha_rad)
        dy = d * math.sin(alpha_rad)
        
        # koncowe współrzędne 
        x = x0 + dx
        y = y0 + dy
        
        wyniki['dx'].append(dx)
        wyniki['dy'].append(dy)
        wyniki['x'].append(x)
        wyniki['y'].append(y)
        

        if analiza_dokladnosci:
            # mD = ma + mb * D 
            mD_m = (mD_mm / 1000.0) + (mD_ppm * 1e-6) * d
            
            # mX i mY zgodnie z prawem propagacji błędów Gaussa
            mx_m = math.sqrt((mD_m * math.cos(alpha_rad))**2 + (d * math.sin(alpha_rad) * mHz_rad)**2)
            my_m = math.sqrt((mD_m * math.sin(alpha_rad))**2 + (d * math.cos(alpha_rad) * mHz_rad)**2)
            
            # błąd położenia punktu mP
            mp_m = math.sqrt(mx_m**2 + my_m**2)
            

            wyniki['mx_mm'].append(mx_m * 1000.0)
            wyniki['my_mm'].append(my_m * 1000.0)
            wyniki['mp_mm'].append(mp_m * 1000.0)
        else:
            wyniki['mx_mm'].append(None)
            wyniki['my_mm'].append(None)
            wyniki['mp_mm'].append(None)
            
    return wyniki
def oblicz_pole_gaussa(obliczone_dane: dict) -> tuple[float, float, int]:
        """
    Oblicza pole powierzchni wieloboku metodą Gaussa (Shoelace formula).
    Filtruje dane wejściowe, odrzucając punkty pomiaru kontrolnego (seria 7_xx).

    Parametry:
    ----------
    obliczone_dane : dict
        Słownik z obliczonymi współrzędnymi płaskimi 'x' oraz 'y'.

    Zwraca:
    -------
    tuple[float, float, int]
        Krotka zawierająca:
        - pole_m2 (float): Pole powierzchni w metrach kwadratowych.
        - pole_ha (float): Pole powierzchni w hektarach.
        - liczba_wierzcholkow (int): Liczba punktów budujących figurę.
    """
        x_wielobok = [] # współrzędne X punktów wieloboku
        y_wielobok = []     # współrzędne Y 
        liczba_wierzcholkow = 0
        
        # bierzemy tylko główny wielobok punkty 1-20 (bez 7_xx
        for i in range(len(obliczone_dane['pkt'])):
            nazwa = obliczone_dane['pkt'][i]
            if "_" not in nazwa:
                x_wielobok.append(obliczone_dane['x'][i])
                y_wielobok.append(obliczone_dane['y'][i])
                liczba_wierzcholkow += 1
                
        n = len(x_wielobok)
        # jeśli <3 punkty nie można utworzyć wieloboku -> pole = 0
        if n < 3:
            return 0.0, 0.0, 0
            
        # Implementacja wzoru Gaussa 
        suma = 0.0
        for i in range(n):
            #  j to następny wierzchołek modulo do z zamknięcia wieloboku
            j = (i + 1) % n  
            suma += x_wielobok[i] * y_wielobok[j] - x_wielobok[j] * y_wielobok[i]
        
        pole_m2 = abs(suma) / 2.0
        pole_ha = pole_m2 / 10000.0  # 1 ha = 10 000 m2 
        
        return pole_m2, pole_ha, liczba_wierzcholkow

def oblicz_regresje(obliczone_dane: dict) -> dict:
    """
    Wyznacza parametry prostej regresji (a, b) metodą najmniejszych kwadratów 
    dla serii punktów 7xx przy użyciu rachunku macierzowego
    
    Funkcja buduje macierz układu oraz wektor obserwacji, a następnie
    rozwiązuje układ równań normalnych. Wylicza wartości estymowane, wektor residuów,
    współczynnik determinacji R^2 oraz błąd standardowy dopasowania Se.

    Parametry:
    ----------
    obliczone_dane : dict
        Słownik zawierający obliczone współrzędne płaskie 'x', 'y' oraz nazwy punktów 'pkt'. 

    Zwraca:
    -------
    dict
        Słownik z wynikami zawierający współczynniki prostej (a, b), liczbę punktów (n),
        miary dopasowania (r2, se) oraz listy współrzędnych, wartości estymowanych i residuów.
    """

    nazwy = []
    x_val = []
    y_val = []
    
    # filtrujemy punkty serii 7 
    for i in range(len(obliczone_dane['pkt'])):
        nazwa = obliczone_dane['pkt'][i]
        if "7_" in nazwa:
            nazwy.append(nazwa)
            x_val.append(obliczone_dane['x'][i])
            y_val.append(obliczone_dane['y'][i])
            
    n = len(x_val)
    if n < 2:
        raise ValueError("Zbyt mało punktów do obliczenia regresji.")
        
    # budujemy macierze układu równań  Y = A * Theta
    # Macierz A  w pierwszej kolumnie X, w drugiej same jedynki
    A = np.zeros((n, 2))
    for i in range(n):
        A[i, 0] = x_val[i]
        A[i, 1] = 1.0
        
    # Wektor Y to współrzędne Y punktów obserwowanych 
    Y = np.array(y_val)
    
    # roziązanie układu równań normalnych Theta = (AtA)^-1 * AtY
    AtA = np.dot(A.T, A)  # Mnożenie macierzy transponowanej przez bazową
    AtY = np.dot(A.T, Y)  # Mnożenie macierzy transponowanej przez wektor Y
    
    # (AtA)^-1 * AtY
    try:
        AtA_odwrotna = np.linalg.inv(AtA)
        Theta = np.dot(AtA_odwrotna, AtY)
    except np.linalg.LinAlgError:
        raise ValueError("Macierz jest osobliwa, punkty ułożone pionowo.")
        
    a = Theta[0]  
    b = Theta[1]  
    
    y_est = []
    residua = []
    ss_res = 0.0
    
    for i in range(n):
        
        y_e = a * x_val[i] + b
        e = y_val[i] - y_e
        y_est.append(y_e)
        residua.append(e)
        ss_res += e ** 2
        
    #  R^2
    y_mean = sum(y_val) / n
    ss_tot = sum((y - y_mean) ** 2 for y in y_val)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    # błąd standardowy dopasowania Se
    se = math.sqrt(ss_res / (n - 2))
    
    return {
        'nazwy': nazwy,
        'x': x_val,
        'y': y_val,
        'y_est': y_est,
        'e': residua,
        'a': a,
        'b': b,
        'n': n,
        'r2': r2,
        'se': se
    }