import os
from parser_danych import wczytaj_i_parsuj_dziennik
from obliczenia import oblicz_wspolrzedne_i_bledy, oblicz_pole_gaussa, oblicz_regresje
from raporty import generuj_raport_obliczen, generuj_raport_regresji
from wizualizacja import rysuj_szkic_sytuacyjny, rysuj_wykres_bledow, rysuj_wykresy_regresji

# stałe określające lokalizację plików wejściowych i wyjściowych
PLIK_WEJSCIOWY = os.path.join("dane", "dziennik_obserwacji.txt")
FOLDER_WYJSCIOWY = "wyniki"

os.makedirs(FOLDER_WYJSCIOWY, exist_ok=True)

metadane = None
obserwacje = None
obliczone_wspolrzedne = None
wyniki_regresji = None

def wyswietl_menu():
    """Wyświetla opcje menu konsolowego w języku polskim."""
    print("\n" + "-"*77)
    print("  Program do przetwarzania i wizualizacji danych z pomiarów tachimetrycznych  ")
    print("-"*77)
    print("1 - Wczytaj i sparsuj dane")
    print("2 - Oblicz współrzędne i błędy punktów")
    print("3 - Oblicz pole powierzchni metodą Gaussa")
    print("4 - Oblicz parametry prostej regresji")
    print("5 - Generuj raporty")
    print("6 - Generuj wizualizacje graficzne")
    print("q - Wyjście z programu")
    print("-"*77)

def main():
    global metadane, obserwacje, obliczone_wspolrzedne, wyniki_regresji
    
    while True:
        wyswietl_menu()
        wybor = input("Wybierz opcję (1-6): ").strip()
        
        if wybor == "1":
            print("\nParsowanie danych z pliku...")
            try:
                metadane, obserwacje = wczytaj_i_parsuj_dziennik(PLIK_WEJSCIOWY)
                print(f"[Sukces] Pomyślnie wczytano dane!")
                print(f" -> Stanowisko: {metadane['stanowisko']} (X0={metadane['x0']}, Y0={metadane['y0']})")
                print(f" -> Liczba zaimportowanych obserwacji: {len(obserwacje['pkt'])}")
                if metadane['mHz_sec'] is None:
                    print(" -> [Info] Brak parametrów dokładności instrumentu w nagłówku. Analiza dokładności będzie pominięta.")
            except FileNotFoundError as e:
                print(f"[Błąd] {e}")
            except Exception as e:
                print(f"[Nieoczekiwany błąd] {e}")
            
        elif wybor == "2":
            print("\nObliczanie współrzędnych i analizy dokładności...")
            if metadane is None or obserwacje is None:
                print("[Błąd] Najpierw musisz wczytać dane! (Wybierz opcję 1)")
            else:
                try:
                    obliczone_wspolrzedne = oblicz_wspolrzedne_i_bledy(metadane, obserwacje)
                    print("[Sukces] Współrzędne i błędy zostały pomyślnie obliczone!")
                    print(f" -> Obliczono współrzędne dla {len(obliczone_wspolrzedne['pkt'])} punktów.")
                except Exception as e:
                    print(f"[Błąd podczas obliczeń]: {e}")
            
        elif wybor == "3":
            print("\n Obliczanie pola powierzchni wieloboku...")
            if obliczone_wspolrzedne is None:
                print("[Błąd] Najpierw musisz obliczyć współrzędne punktów! (Wybierz opcję 2)")
            else:
                try:
                    pole_m2, pole_ha, wierzcholki = oblicz_pole_gaussa(obliczone_wspolrzedne)
                    print(f"[Sukces] Pole powierzchni zostało obliczone metodą Gaussa!")
                    print(f" -> Liczba wierzchołków wieloboku: {wierzcholki}")
                    print(f" -> Pole powierzchni: {pole_m2:.3f} m2")
                    print(f" -> Pole powierzchni: {pole_ha:.6f} ha")

                    # Dorzucamy obliczone pole do słownika globalnego, aby raport miał do niego dostęp
                    obliczone_wspolrzedne['pole_gaussa'] = (pole_m2, pole_ha, wierzcholki)
                except Exception as e:
                    print(f"[Błąd podczas obliczania pola]: {e}")
            
        elif wybor == "4":
            print("\nAnaliza regresji liniowej dla serii 7...")
            if obliczone_wspolrzedne is None:
                print("[Błąd] Najpierw musisz obliczyć współrzędne punktów! (Wybierz opcję 2)")
            else:
                try:
                    wyniki_regresji = oblicz_regresje(obliczone_wspolrzedne)
                    print("[Sukces] Obliczono parametry regresji liniowej!")
                    print(f" -> Równanie prostej: Y = {wyniki_regresji['a']:+.4f} * X {wyniki_regresji['b']:+.4f}")
                    print(f" -> Współczynnik dopasowania R^2: {wyniki_regresji['r2']:.4f}")
                except Exception as e:
                    print(f"[Błąd podczas obliczania regresji]: {e}")
            
        elif wybor == "5":
            print("\nZapisywanie raportów tekstowych...")
            if obliczone_wspolrzedne is None:
                print("[Błąd] Brak wyników! Najpierw wykonaj obliczenia (Opcja 2 i 3).")
            else:
                try:
                    chce_bledy = True
                    if obliczone_wspolrzedne['mx_mm'][0] is not None:
                        odp = input("Czy dołączyć analizę dokładności do raportu? (T/N): ").strip().upper()
                        if odp == 'N':
                            chce_bledy = False
                    # Generowanie raportu głównego
                    sciezka_glownego = generuj_raport_obliczen(metadane, obliczone_wspolrzedne, FOLDER_WYJSCIOWY, chce_bledy)
                    print(f"[Sukces] Raport z obliczeń zapisany: {sciezka_glownego}")
                    
                    # Generowanie raportu regresji (jeśli została obliczona)
                    if wyniki_regresji is not None:
                        sciezka_regresji = generuj_raport_regresji(wyniki_regresji, FOLDER_WYJSCIOWY)
                        print(f"[Sukces] Raport z regresji zapisany: {sciezka_regresji}")
                    else:
                        print(" -> [Info] Pominięto raport z regresji (brak wykonanych obliczeń - użyj Opcji 4).")
                        
                except Exception as e:
                    print(f"[Błąd podczas generowania raportów]: {e}")


            
        elif wybor == "6":
            print("\n Generowanie wykresów...")
            if obliczone_wspolrzedne is None:
                print("[Błąd] Brak wyników! Najpierw wykonaj obliczenia (Opcja 2).")
            else:
                try:
                    # 1. Szkic sytuacyjny
                    s1 = rysuj_szkic_sytuacyjny(metadane, obliczone_wspolrzedne, FOLDER_WYJSCIOWY)
                    print(f"[Sukces] Wygenerowano szkic sytuacyjny: {s1}")
                    
                    # 2. Wykres błędów mP
                    s2 = rysuj_wykres_bledow(obliczone_wspolrzedne, FOLDER_WYJSCIOWY)
                    if s2:
                        print(f"[Sukces] Wygenerowano wykres błędów mP: {s2}")
                    else:
                        print(" -> [Info] Wykres błędów pominięty (brak danych dokładnościowych).")
                        
                    # 3. Wykresy regresji (jeśli została policzona)
                    if wyniki_regresji is not None:
                        s3 = rysuj_wykresy_regresji(wyniki_regresji, FOLDER_WYJSCIOWY)
                        print(f"[Sukces] Wygenerowano wykres regresji: {s3}")
                    else:
                        print(" -> [Info] Wykres regresji pominięty (brak wykonanych obliczeń - użyj Opcji 4).")
                        
                except Exception as e:
                    print(f"[Błąd podczas generowania wykresów]: {e}")
            
        elif wybor == "q":
            print("\nProgram został zamknięty.")
            break
            
        else:
            print("\n[Błąd] Nieprawidłowy wybór!")

if __name__ == "__main__":
    main()