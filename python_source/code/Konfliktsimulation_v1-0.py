'''Programm zur Durchführung von Konfliktsimulationen

Struktur des Codes:
1) Imports
2) Initialisierung
3) Dataframe-Management
4) Fenster-Management
5) Programmfunktionen
    (A) Gefecht
    (B) Truppenverwaltung
    (C) Tabellen einsehen
    (D) Runde beenden
6) Ergebnisprotokollierung

Corinna Keupp und Johannes Leitgeb, März 2021'''


# 1) I M P O R T S

import PySimpleGUI as sg
import pandas as pd
import pickle
import math
import statistics
import random
import datetime
import os


# 2) I N I T I A L I S I E R U N G

def main():
    """Deklariert globale Variablen und initialisiert den Simulations-Loop"""

    sg.theme('LightGrey1')

    global name
    global runde
    global zeit
    global results_csv
    global vernichtet
    global startzeit
    global england_df
    global frankreich_df

    resolve = False
    while not resolve:
        time, mode, name = start_window()

        if mode == "neu":
            initialize()
            runde = 0
            startzeit = time
            zeit = (startzeit + datetime.timedelta(hours=runde)).time()
            results_csv = pd.DataFrame(
                columns=['Zeitpunkt', 'Ort', 'Angreifer', 'Truppen_Angreifer', 'Truppen_Verteidiger', 'Verhältnis', 'Resultat'])
            vernichtet = []
            simulation = True
            resolve = True
        elif mode == "laden":
            if os.path.exists(f"../results/{name}") and name != "":
                standings = pickle.load(open(path_to_results() + "/previous_rounds.pkl", "rb"))
                runde = standings["runde"]
                zeit = standings["zeit"]
                startzeit = standings["startzeit"]
                england_df = standings["england_df"]
                frankreich_df = standings["frankreich_df"]
                vernichtet = standings["vernichtet"]
                if os.path.exists(path_to_results() + "/Results.csv"):
                    results_csv = pd.read_csv(path_to_results() + "/Results.csv", sep=";")
                else:
                    results_csv = pd.DataFrame(columns=['Zeitpunkt', 'Ort', 'Angreifer', 'Truppen_Angreifer', 'Truppen_Verteidiger', 'Verhältnis', 'Resultat'])
                global troops_E
                troops_E = england_df.index
                global troops_F
                troops_F = frankreich_df.index
                simulation = True
                resolve = True
            else:
                sg.popup('Der angegebene Ordner existiert nicht in "results"!')
                simulation = False
                resolve = False
        elif mode == "stopp":
            simulation = False
            resolve = True
            name = None
            runde = None
            zeit = None
            results_csv = None
            vernichtet = None
            startzeit = None
            england_df = None
            frankreich_df = None

    while simulation:
        simulation = overview_window()

    save_files()


def path_to_data():
    """Gibt den relativen Pfad zu den benötigten Daten zurück"""
    datapath = "../data"
    return datapath


def path_to_results():
    """Gibt den relativen Pfad zur Ergebnisprotokollierung zurück und erzeugt ihn, falls er nicht vorhanden ist"""
    global name
    respath = f"../results/{name}"
    if not os.path.exists(respath):
        os.makedirs(respath)
    return respath


def initialize():
    """Bereitet die eingegebenen Datentabellen als globale Pandas-Dataframes auf"""
    global england_df
    england_df = normalize(path_to_data()+"/England_Start.csv")
    global frankreich_df
    frankreich_df = normalize(path_to_data()+"/Frankreich_Start.csv")
    global troops_E
    troops_E = england_df.index
    global troops_F
    troops_F = frankreich_df.index


# 3) D A T A F R A M E - M A N A G E M E N T

def experience_word_to_number(erfahrung):
    """Transformiert Erfahrungsangaben in numerische Werte"""
    if erfahrung.lower() == "unerfahren":
        erfahrung_zahl = 0
    elif erfahrung.lower() == "normal":
        erfahrung_zahl = 1
    elif erfahrung.lower() == "erfahren":
        erfahrung_zahl = 2
    else:
        print("Die Truppe scheint Probleme bei der Erfahrung zu haben")
        erfahrung_zahl = -1
    return erfahrung_zahl


def normalize(datapath):
    """Erstellt benötigte Spalten und Werte für die eingegebenen Datentabellen"""
    dataframe = pd.read_csv(datapath, sep=";", encoding="utf-8", index_col="name")

    # Columns die auf existierenden columns bestehen
    dataframe["erfahrung_zahl"] = 0
    for index, row in dataframe.iterrows():
        xp = row["erfahrung_wort"]
        dataframe.at[index,"erfahrung_zahl"] = experience_word_to_number(xp)
    dataframe["staerke_aktuell"] = dataframe["staerke_beginn"]

    # neue Columns mit pre-set-values
    # malus
    dataframe["muede"] = 0
    dataframe["flucht"] = 0
    # bonus
    dataframe["eingegraben"] = 0
    # sonstiges
    dataframe["standort_aktuell"] = None
    dataframe["standort_letzteRunde"] = None
    columns = ["brigade","name_vollstaendig","typ","staerke_beginn","staerke_aktuell","erfahrung_wort","erfahrung_zahl","muede", "flucht", "eingegraben", "standort_aktuell","standort_letzteRunde"]
    dataframe = dataframe[columns]

    name = datapath.replace("_Start.csv", "_aktuell.csv")
    dataframe.to_csv(name, sep=";", index=True, encoding="utf-8")

    return dataframe


def reload_df(side):
    """Lädt die Dataframes aus den csv-Dateien neu"""
    if side == "e":
        global england_df
        england_df = pd.read_csv(path_to_data()+"/England_aktuell.csv", sep=";", encoding="utf-8", index_col="name")
        return england_df
    elif side =="f":
        global frankreich_df
        frankreich_df = pd.read_csv(path_to_data()+"/Frankreich_aktuell.csv", sep=";", encoding="utf-8", index_col="name")
        return frankreich_df


def save_df (df, side):
    """Speichert die Dataframes als csv-Dateien"""
    if side == "e":
        df.to_csv(path_to_data() + "/England_aktuell.csv", index=True, sep=";")
    elif side == "f":
        df.to_csv(path_to_data() + "/Frankreich_aktuell.csv", index=True, sep=";")


# 4) F E N S T E R - M A N A G E M E N T

def ini_window():
    """Fenster zur Vergabe eines Namen und einer Startzeit für eine neue Simulation"""
    layout_initialize = [
        [sg.Text("Geben Sie einen Namen für die Simulation ein (Ohne Leerzeichen/Sonderzeichen): "),
         sg.InputText("", key="name")],
        [sg.Text("Geben Sie eine Startzeit an: "),
         sg.Spin(values=[i for i in range(0, 24)], initial_value=7, size=(6, 1), key="zeit")],  # Probleme mit Format?
        [sg.Button("Weiter")]]
    win1 = sg.Window(title="Initialisieren", layout=layout_initialize, grab_anywhere=True, resizable=True)

    while True:
        event, values = win1.read()
        time = values["zeit"]
        name = values["name"]
        modus = "neu"
        if event == "Weiter":
            win1.close()
            break

        if event == sg.WIN_CLOSED:
            modus = "stopp"
            time = 00
            name = 00
            win1.close()
            break

    return time, name, modus

def start_window():
    """Fenster zur Auswahl einer neuen oder einer bereits bestehenden Simulation"""
    layout_start = [[sg.Button('Neue Simulation starten')],
                    [sg.Button('Gespeicherte Simulation aufrufen')],
                    [sg.Button('Beenden')]]

    win0 = sg.Window(title="Simulationsbeginn", layout= layout_start, grab_anywhere=True, resizable=True,
                     element_justification="center", size=(500,500), margins= (100,100))

    h = 0
    modus = ""
    name = ""
    while True:
        event, values = win0.read()
        if event == "Neue Simulation starten":
            h, name, modus = ini_window()
            #h = int(sg.popup_get_text("Startzeit im Format HH: ", default_text=00))
            time = datetime.datetime(1, 1, 1, hour=h)
            win0.close()
            break
        if event == "Gespeicherte Simulation aufrufen":
            modus = "laden"
            name = sg.popup_get_text("Name des Ordners in Results: ", default_text="")
            time = None
            win0.close()
            break
        if event == sg.WIN_CLOSED or event == "Beenden":
            modus = "stopp"
            time = None
            win0.close()
            break
    return time, modus, name


def overview_window():
    """Fenster zum Simulationsmanagement"""
    global runde
    global zeit
    global england_df
    global frankreich_df
    simulation = False

    layout_overview = [
        [sg.Text("Runde:", auto_size_text=True, font=("Arial", 13)), sg.Text(runde, key="round", font=("Arial", 14)),
         sg.Text("||", font=("",15)),#⌛ ||
         sg.Text("Uhrzeit:", key="clock", font=("Arial", 13)), sg.Text(zeit, key="time", font=("Arial", 14))],
        [sg.Button("Gefecht", size=(25, 4), font=("Arial", 13))],
        [sg.Button("Truppenverwaltung", size=(25, 4), font=("Arial", 13))],
        [sg.Button("Tabellen einsehen", size=(25, 4), font=("Arial", 13))],
        [sg.Button("Simulationsstand speichern", size=(25, 4), font=("Arial", 13))],
        [sg.Button("Runde beenden", size=(25, 4), font=("Arial", 13))],
        [sg.Button("Simulation beenden", size=(25, 4), font=("Arial", 13))]]

    win1 = sg.Window(title='Konfliktsimulation', layout=layout_overview, margins=(100, 50), grab_anywhere=True, resizable=True)
    while True:
        ev1, val1 = win1.read()
        if ev1 == 'Tabellen einsehen':
            show_dataframes()
        if ev1 == 'Gefecht':
            win1.hide()
            fight_window()
            win1.un_hide()
            england_df = reload_df("e")
            frankreich_df = reload_df("f")
        if ev1 == 'Truppenverwaltung':
            win1.hide()
            troopupdate()
            win1.un_hide()
        if ev1 == 'Simulationsstand speichern':
            save_files()
            sg.popup("Simulationsstand wurde gespeichert!")
        if ev1 == 'Runde beenden':
            win1.finalize()
            runde += 1
            zeit = (startzeit + datetime.timedelta(hours=runde)).time()
            england_df = round_update(england_df)
            frankreich_df = round_update(frankreich_df)
            save_df(england_df, "e")
            save_df(frankreich_df, "f")
            england_df = reload_df("e")
            frankreich_df = reload_df("f")
            win1.find_element("round").update(runde)
            win1.find_element("time").update(zeit)
        if ev1 == 'Simulation beenden':
            england_df = reload_df("e")
            frankreich_df = reload_df("f")
            win1.close()
            simulation = show_winner()
            break
        if ev1 == sg.WIN_CLOSED or ev1 == 'Beenden':  # if user closes window or clicks cancel
            simulation = False
            win1.close()
            break
    return simulation


def fight_window():
    """Fenster zur Initialisierung eines Gefechts"""
    col_start = [[sg.Text("Ort: "), sg.InputText("z.B. London", key="place")], [sg.Checkbox('Überraschungsangriff?', default=False, key="surprise")],
                     [sg.Text("Angreifer"), sg.Drop(values=('England', 'Frankreich'), size=(20, 1), key="attacker", default_value="England")],
                     [sg.Button('Hauptmenü'), sg.Button('Weiter')]]


    troops_E_show, troops_F_show = remove_destroyed()

    col_E = [[sg.Text("Englische Truppen:", size=(30, 1))], *[[sg.Checkbox(troops_E_show[x], key="e"+str(x)),] for x in range(len(troops_E_show))]]
    col_F = [[(sg.Text("Französische Truppen:", size=(30, 1)))],  *[[sg.Checkbox(troops_F_show[y], key="f"+str(y)),] for y in range(len(troops_F_show))]]

    layoutgefecht = [[sg.Text("G E F E C H T", font=("Arial", 20))],
                     [sg.Column(col_start), sg.Column(col_E), sg.Column(col_F)]]

    win2 = sg.Window('Gefecht', layoutgefecht, grab_anywhere=True, resizable=True)

    engTruppen = []
    franzTruppen = []

    while True:
        ev2, vals2 = win2.Read()
        if ev2 == "Weiter":
            for x in range(len(troops_E_show)):
                if vals2["e"+str(x)] == True:
                    engTruppen.append(troops_E_show[x])
            for y in range(len(troops_F_show)):
                if vals2["f"+str(y)] == True:
                    franzTruppen.append(troops_F_show[y])
            if franzTruppen == [] or engTruppen == []:
                sg.popup("Es wurden keine Truppen ausgewählt!")
                win2.close()
                break
            ort = vals2["place"]
            surprise = vals2["surprise"]
            if vals2["attacker"] == "England":
                attacker = "e"
            elif vals2["attacker"] == "Frankreich":
                attacker = "f"
            fleeing, fleeing_troops = fleeing_check(engTruppen,franzTruppen,attacker)
            if not fleeing:
                win2.Close()
                attacker_bonus, defender_bonus, resp = man_boni_window()
                if resp == "abbrechen":
                    break
                output_fight_window(ort,attacker,engTruppen,franzTruppen,attacker_bonus,defender_bonus)
                break
            else:
                sg. popup(f"Folgende Truppen sind auf der Flucht und können nicht angreifen: {fleeing_troops}")
                win2.close()
                break
        if ev2 == sg.WIN_CLOSED or ev2 == 'Hauptmenü':
            win2.Close()
            break


def man_boni_window():
    """Fenster zur Eingabe manueller Boni"""
    angreifer = 0
    verteidiger = 0

    columnAng = [[sg.Text("geografischer Vorteil Angreifer:"), sg.Radio('Ja', "RADIO1", key = "geoAng"),sg.Radio('Nein', "RADIO1", default=True)],
                 [sg.Text("Gibt es sonstige Vorteile für den Angreifer? "), sg.Spin([i for i in range(0,11)], initial_value=0, key="sonsAng")],
                 ]

    columnVer = [[sg.Text("geografischer Vorteil Verteidiger:"), sg.Radio('Ja', "RADIO2", key="geoVer"),sg.Radio('Nein', "RADIO2", default=True)],
                 [sg.Text("Gibt es sonstige Vorteile für den Verteidiger? "), sg.Spin([i for i in range(0,11)], initial_value=0, key="sonsVer")],
                 ]

    layout = [[sg.Text('Eingabe manueller Vorteile', font= 30)],
             [sg.Column(columnAng), sg.Column(columnVer)],
              [sg.Button("abbrechen"), sg.Button("weiter")]
              ### bei zurück passiert nichts ??????????????????
              ]

    window = sg.Window("Manuelle Boni", layout, grab_anywhere=True, resizable=True)
    while True:
        event, values = window.read()

        if event is None:
            break
        if event == "weiter":
            if values["geoAng"] == True:
                angreifer += 1
            if values["geoVer"] == True:
                verteidiger = + 1

            sonsValueAng = values["sonsAng"]
            angreifer = angreifer + sonsValueAng

            sonsValueVer = values["sonsVer"]
            verteidiger = verteidiger + sonsValueVer
            resp = "OK"
            window.close()
        elif event == "abbrechen":
            resp = event
            window.close()
            break
    return int(angreifer), int(verteidiger), resp


def output_fight_window (ort, attacker, engTruppen, franzTruppen, attacker_bonus, defender_bonus):
    """Fenster zur Ausgabe der Kampfergebnisse"""
    layout_output = [[sg.Output(key="-OUTPUT-", size=(100,20), font="Courier 15", visible=False)],[sg.B("Berechnung starten"),sg.B("Close")]]
    win4 = sg.Window('Gefechtsverlauf', layout_output, grab_anywhere=True, resizable=True)
    while True:
        ev4, vals4 = win4.Read()
        win4["Berechnung starten"].Update(disabled=True, visible=False)
        if ev4 == "Berechnung starten":
            win4["-OUTPUT-"].Update(visible=True)
            fight(ort, attacker, engTruppen, franzTruppen, attacker_bonus, defender_bonus)
        if ev4 == sg.WIN_CLOSED or ev4=="Close":
            win4.Close()
            break


def troopupdate():
    """Fenster zur Truppenverwaltung"""
    troops_E_show, troops_F_show = remove_destroyed()

    columnEngland =[[sg.Text("Truppenauswahl England: ")],
                    [sg.InputOptionMenu(values=troops_E_show , key=("Troop_E"))],
                    [sg.Button("Eingraben", key=("eingraben_E")), sg.Button("Ausgraben", key=("ausgraben_E"))],
                    [sg.Button("Bewegen", key=("bewegen_E"))],
                    [sg.Button("Erkunden", key=("erkunden_E"))],
                    ]

    columnFrankreich =[[sg.Text("Truppenauswahl Frankreich: ")],
                     [sg.InputOptionMenu(values=troops_F_show, key=("Troop_F"))],
                     [sg.Button("Eingraben", key=("eingraben_F")), sg.Button("Ausgraben", key=("ausgraben_F"))],
                     [sg.Button("Bewegen", key=("bewegen_F"))],
                     [sg.Button("Erkunden", key=("erkunden_F"))],
                       ]

    layout_update = [[sg.Column(columnEngland, background_color='lightyellow', element_justification='c'),
                      sg.Column(columnFrankreich, background_color='lightblue', element_justification='c')],
                     [sg.Output(size=(50,10), key='-OUTPUT-')],
                     [sg.Button("Schließen")],
                     ]

    window = sg.Window(title='Truppenaktualisierung', layout=layout_update, margins=(300, 200), grab_anywhere=True, resizable=True)

    while True:
        event, values = window.read()
        if event == "eingraben_F":
            duration = duration_window()

            if event == "Cancel" or duration == "" or duration is None:
            #if event == "Cancel" or math.isnan(duration) == True:
                break #break closes the window - aber keine error message

            duration = int(duration)
            #Cancel - was dann?????
            troopF = values["Troop_F"]
            print("Ausgewählte Einheit: " + troopF)
            dig_in(troopF, frankreich_df, duration)
            report_entry("F", "eingraben", str(troopF), f"{duration}")

            save_df(frankreich_df, "f")


        if event == "ausgraben_F":
            duration = duration_window()
            if event == "Cancel" or duration == "" or duration is None:
                break  # break closes the window - aber keine error message
            duration = int(duration)
            # Cancel - was dann?????
            troopF = values["Troop_F"]
            print("Ausgewählte Einheit: " + troopF)
            dig_out(troopF, frankreich_df, duration)
            report_entry("F", "ausgraben", str(troopF), f"{duration}")

            save_df(frankreich_df, "f")


        if event == "bewegen_F":
            troopF = values["Troop_F"]
            new_location = sg.popup_get_text("Neuer Standort: ", title="Bewegen")
            if event == "Cancel" or new_location == "" or new_location is None:
                break
            print("Ausgewählte Einheit: " + troopF)
            movement(troopF, frankreich_df, new_location)
            report_entry("F","bewegung",str(troopF),f"Neuer Standort: {new_location}")

            save_df(frankreich_df, "f")


        if event == "erkunden_F":
            troopF = values["Troop_F"]
            new_location = sg.popup_get_text("Neuer Standort: ", title="Erkunden")
            if new_location == "" or event == "Cancel" or new_location is None:
                break
            see = sg.popup_get_text("Was kann gesehen werden? ")
            if see == None or event == "Cancel" or see is None:
                break
            lookout(troopF, frankreich_df, new_location, see)
            print("Ausgewählte Einheit: " + troopF)
            print("Kann folgendes sehen: " + see)
            report_entry("F", "spähen", str(troopF), f"{see}")

            save_df(frankreich_df, "f")


        if event == "eingraben_E":
            # new_location = sg.popup_get_text("Standort: ")
            duration = duration_window()
            if event == "Cancel" or duration == "" or duration is None:
                break  # break closes the window - aber keine error message
            duration = int(duration)
            # Cancel - was dann?????
            troopE = values["Troop_E"]
            print("Ausgewählte Einheit: " + troopE)
            dig_in(troopE, england_df, duration)
            report_entry("E", "eingraben", str(troopE), f"{duration}")

            save_df(england_df, "e")

        if event == "ausgraben_E":
            duration = duration_window()
            if duration == "" or event == "Cancel" or duration is None:
                break
            duration = int(duration)
            troopE = values["Troop_E"]
            print("Ausgewählte Einheit: " + troopE)
            dig_out(troopE, england_df, duration)
            report_entry("E", "ausgraben", str(troopE), f"{duration}")

            save_df(england_df, "e")

        if event == "bewegen_E":
            troopE = values["Troop_E"]
            new_location = sg.popup_get_text("Neuer Standort: ",title="Bewegen")
            if new_location == "" or event == "Cancel" or new_location is None:
                break
            print("Ausgewählte Einheit: " + troopE)
            movement(troopE, england_df, new_location)
            report_entry("E", "bewegung", str(troopE), f"Neuer Standort: {new_location}")

            save_df(england_df, "e")

        if event == "erkunden_E":
            troopE = values["Troop_E"]
            new_location = sg.popup_get_text("Neuer Standort: ", title="Erkunden")
            if new_location == "" or event == "Cancel" or new_location is None:
                break
            see = sg.popup_get_text("Was kann gesehen werden? ", title="Beobachtung")
            if see == "" or event == "Cancel" or see is None:
                break
            lookout(troopE, england_df, new_location, see)
            report_entry("E", "spähen", str(troopE), f"{see}")
            print("Ausgewählte Einheit: " + troopE)
            print("Kann folgendes sehen: " + see)

            save_df(england_df, "e")

        if event == "Schließen":
            save_df(frankreich_df, "f")
            save_df(england_df, "e")
            window.close()
            break
        if event is None:
            break
    window.close()


def duration_window():
    """Fenster zur Eingabe einer Dauer in Runden"""
    duration = ""
    layout_duration = [
        [sg.Text("Wie lange wird die Einheit beschäftig sein: "),
         sg.Spin(values=[i for i in range(0, 24)], initial_value=1, size=(6, 1), key="zeit")],  # MAXIMALE ANZAHL???
        [sg.Button("Ok"), sg.Button("Abbrechen")]]
    win_dur = sg.Window(title="Dauer", layout=layout_duration, grab_anywhere=True, resizable=True)

    while True:
        event, values = win_dur.read()

        if event == "Abbrechen" or event == sg.WIN_CLOSED:
            win_dur.close()
            break
        if event == "Ok":
            duration = values["zeit"]
            win_dur.close()
            break
    return duration


def show_dataframes():
    """Fenster zur Anzeige der Dataframes"""
    sg.set_options(auto_size_buttons=True)

    df_E = pd.read_csv(path_to_data()+"/England_aktuell.csv", sep=';', engine='python', header=None)
    header_list_E = df_E.iloc[0].tolist()
    data_E = df_E[1:].values.tolist()

    df_F = pd.read_csv(path_to_data()+"/Frankreich_aktuell.csv", sep=';', engine='python', header=None)
    header_list_F = df_F.iloc[0].tolist()
    data_F = df_F[1:].values.tolist()

    layout = [
        [sg.Text(" England ", background_color="lightblue", relief="sunken", font=("Arial", 15), pad=(10,10) )],
        [sg.Table(values=data_E,
                  headings=header_list_E,
                  display_row_numbers=False,
                  auto_size_columns=True,
                  num_rows=min(25, len(data_E)))],
        [sg.Text(" Frankreich ", background_color="lightblue", relief="sunken", font=("Arial", 15), pad=(10,10))],
        [sg.Table(values=data_F,
                  headings=header_list_F,
                  display_row_numbers=False,
                  auto_size_columns=True,
                  num_rows=min(25, len(data_F)))],
        [sg.Button("Fenster schließen")]
    ]

    window = sg.Window('Tabellen einsehen', layout, grab_anywhere=True, resizable=True, element_justification="center")
    while True:
        event, values = window.read()
        if event == "Fenster schließen" or event == sg.WIN_CLOSED:
            window.close()
            break


def show_winner():
    """Fenster zur Auswahl eines Gewinners am Ende der Simulation"""
    Simulation = False
    layout = [[sg.Text('Die Simulation ist beendet.')],
              [sg.Text("")],
              [sg.Text("Englische Truppen: "), sg.Text(england_df["staerke_aktuell"].sum(skipna= True) ), sg.Text("/"),
               sg.Text(england_df["staerke_beginn"].sum(skipna= True))],
              [sg.Text("Französische Truppen: "), sg.Text(frankreich_df["staerke_aktuell"].sum(skipna=True)), sg.Text("/"),
               sg.Text(frankreich_df["staerke_beginn"].sum(skipna=True))],
              [sg.Text("")],
              [sg.Text("Damit gewinnt: "), sg.Combo(["England", "Frankreich", "Unentschieden"], default_value="Auswählen", key="winner")],
              [sg.Submit()]]

    window_w = sg.Window('Window Title', layout, grab_anywhere=True, resizable=True)

    while True:  # The Event Loop
        event, values = window_w.read()
        winner = values['winner']
        if winner is None or winner == "":
            window_w.close()
            return Simulation
        else:
            winner = values['winner']
        if event == "Submit":
            window_w.close()

        if winner == "England":
            win_image("E")
            return Simulation

        elif winner == "Frankreich":
            win_image("F")
            return Simulation

        else:
            window_w.close()
            sg.popup("Keiner gewinnt. :(")
            return Simulation

        if event == sg.WIN_CLOSED or event == 'Exit':
            break
    return Simulation


def win_image(win):
    """Fenster zur Ausgabe des Gewinners"""
    if win == "F":
        Frankreich_image = path_to_data() + "/800px-Flag_of_France.png"
        layout = [[sg.Text('Die Simulation ist beendet.')],
    [sg.Image(Frankreich_image)],
              [sg.Text("Der Gewinner ist Frankreich.")]]
    if win == "E":
        England_image = path_to_data() + "/800px-Flag_of_the_United_Kingdom.png"
        layout = [[sg.Text('Die Simulation ist beendet.')],
                  [sg.Image(England_image)],
                  [sg.Text("Der Gewinner ist England")]]
    window = sg.Window("end", layout, grab_anywhere=True, resizable=True)

    simulation = False

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
    return simulation


# 5) P R O G R A M M F U N K T I O N E N

# (A) G E F E C H T

def fight(ort, attacker, englischeTruppen, franzTruppen, attacker_bonus, defender_bonus):
    """Kalkulation des Gefechtsausgangs"""
    verh = ratio(englischeTruppen, franzTruppen, attacker, attacker_bonus, defender_bonus)  # Ausgabeformat: a:v
    print("Dies ergibt ein Verhältnis von: " + verh)
    res_a, res_v = check_results(verh, roll_dice())
    print(f'Angreifer: {res_a}, Verteidiger: {res_v}')

    if attacker == "e":
        generateBattleResults(zeit, ort, attacker, englischeTruppen, franzTruppen, verh, res_a, res_v)
        for t in englischeTruppen:
            england_aktualisiert = take_damage(t, res_a, england_df, "E", ort)
        for t in franzTruppen:
            frankreich_aktualisiert = take_damage(t, res_v, frankreich_df, "F", ort)
    elif attacker == "f":
        generateBattleResults(zeit, ort, attacker, franzTruppen, englischeTruppen, verh, res_a, res_v)
        for t in englischeTruppen:
            england_aktualisiert = take_damage(t, res_v, england_df, "E", ort)
        for t in franzTruppen:
            frankreich_aktualisiert = take_damage(t, res_a, frankreich_df, "F", ort)
    england_aktualisiert.to_csv(path_to_data() + "/England_aktuell.csv", index=True, sep=";")
    frankreich_aktualisiert.to_csv(path_to_data() + "/Frankreich_aktuell.csv", index=True, sep=";")


def strength(name, side):
    """Funktion zur Berechnung der Anzahl der Männer in einer Einheit zurück, falls es sich um Artillerie handelt wird
    diese erst berechnet"""

    if side == "F":
        manpower_currently = frankreich_df._get_value(name, "staerke_aktuell")
        manpower_begin = frankreich_df._get_value(name, "staerke_beginn")
        type = frankreich_df._get_value(name, "typ").lower()

    elif side == "E":
        manpower_currently = england_df._get_value(name, "staerke_aktuell")
        manpower_begin = england_df._get_value(name, "staerke_beginn")
        type = england_df._get_value(name, "typ").lower()

    if "artillerie" in type and manpower_currently == manpower_begin:
        geschuetze = manpower_begin
        manpower_currently = geschuetze * 100
    return manpower_currently


def tired(name, side):
    """Funktion zur Subtraktion des Malus, wenn müde"""
    malus = 0
    if side =="F":
        tired = frankreich_df._get_value(name, "muede")
    elif side == "E":
        tired = england_df._get_value(name, "muede")

    if tired > 0:
        malus += 1
    return malus


def getaway(name, side):
    """Funktion zur Subtraktion des Malus, wenn auf der Flucht"""
    malus = 0

    if side =="F":
        getaway = frankreich_df._get_value(name, "flucht")
    elif side == "E":
        getaway = england_df._get_value(name, "flucht")
    if getaway > 0:
        malus += 1
    return malus


def entrenched(troops, side):
    """Funktion zur Berechnung des Bonus, wenn eingegraben"""
    bonus = 0
    unit_entrenched = False

    for name in troops:
        if side =="F":
            entrenched = frankreich_df._get_value(name, "eingegraben")
        elif side == "E":
            entrenched = england_df._get_value(name, "eingegraben")

        if entrenched > 0:
            bonus = 1
            unit_entrenched = True
            print(f"Eine Truppe ist eingegraben und dadurch erhält folgende Seite einen Bonus: {side}")
            break

    return bonus
    # muss plus gemacht werden


def fleeing_check(troops_E,troops_F,attacker):
    """Funktion zum Test, ob beim Angreifer Truppen auf der Flucht sind, die laut Regelwerk nicht angreifen können"""
    fleeing = False
    fleeing_troops = []
    if attacker == "f":
        for troop in troops_F:
            value = frankreich_df.loc[troop, "flucht"]
            if value > 0:
                fleeing = True
                fleeing_troops.append(troop)
    elif attacker == "e":
        for troop in troops_E:
            value = england_df.loc[troop, "flucht"]
            if value > 0:
                fleeing = True
                fleeing_troops.append(troop)
                break
    return fleeing, fleeing_troops


def artillery_check(troops_E, troops_F):
    """Funktion zur Berechnung des Bonus aus artilleristischer Überlegenheit"""
    artillery_veryStrong_F = False
    artillery_veryStrong_E = False

    artillery_strong_F = False
    artillery_strong_E = False

    for einheit in troops_F:
        typ = frankreich_df._get_value(einheit, "typ")
        if "schwere" in typ.lower():
            artillery_veryStrong_F = True
        elif "artillerie" in typ.lower():
            artillery_strong_F = True

    for einheit in troops_E:
        typ = england_df._get_value(einheit, "typ")
        if "schwere" in typ.lower():
            artillery_veryStrong_E = True
        elif "artillerie" in typ.lower():
            artillery_strong_E = True

    if artillery_veryStrong_E:
        eng = 2
    elif artillery_strong_E:
        eng = 1
    else:
        eng = 0

    if artillery_veryStrong_F:
        fre = 2
    elif artillery_strong_F:
        fre = 1
    else:
        fre = 0

    bonusE = eng - fre
    if bonusE < 0:
        bonusE = 0
    bonusF = fre - eng
    if bonusF < 0:
        bonusF = 0

    print(f'Die englischen Truppen erhalten einen artilleristischen Vorteil von {bonusE}.')
    print(f'Die französischen Truppen erhalten einen artilleristischen Vorteil von {bonusF}.')
    return bonusE, bonusF


def experience_check(troops_E, troops_F):
    """Funktion zur Berechnung des Bonus aus Erfahrungsvorteilen"""
    values_E = []
    values_F = []

    for einheit in troops_E:
        values_E.append(england_df._get_value(einheit, "erfahrung_zahl"))
    for einheit in troops_F:
        values_F.append(frankreich_df._get_value(einheit, "erfahrung_zahl"))

    x_E = statistics.mean(values_E)
    x_F = statistics.mean(values_F)

    if x_E > x_F:
        winner = "e"
        maximum = max(values_E)
        minimum = min(values_F)
        print("Die englischen Truppen erhalten einen Erfahrungsbonus.")
    elif x_F > x_E:
        winner = "f"
        maximum = max(values_F)
        minimum = min(values_E)
        print("Die französischen Truppen erhalten einen Erfahrungsbonus.")
    else:
        winner = "none"
        maximum = 0
        minimum = 0
        print("Keine der beiden Seiten erhält einen Erfahrungsbonus.")

    bonus = maximum - minimum

    return winner, bonus


def normalize_malus_F(troopsF):
    """Funktion zur Normalisierung der Malus-Werte für Frankreich"""
    malus_muede = False
    malus_flucht = False
    malus_gesamt = 0

    for einheit in troopsF:
        if tired(einheit, "F") == 1:
            malus_muede = True
        if getaway(einheit, "F") == 1:
            malus_flucht = True

    if malus_muede == True and malus_flucht == True:
        malus_gesamt = 2
        print("Die französischen Einheiten sind müde und auf der Flucht. Malus: 2.")
    elif malus_muede == True and malus_flucht == False:
        malus_gesamt = 1
        print("Die französischen Einheiten sind müde. Malus: 1.")
    elif malus_muede == False and malus_flucht == True:
        malus_gesamt = 1
        print("Die französischen Einheiten sind auf der Flucht. Malus: 1.")
    else:
        malus_gesamt = 0

    return malus_gesamt


def normalize_malus_E(troopsE):
    """Funktion zur Normalisierung der Malus-Werte für England"""
    malus_muede = False
    malus_flucht = False  #
    malus_gesamt = 0

    for einheit in troopsE:
        if tired(einheit, "E") == 1:
            malus_muede = True
        if getaway(einheit, "E") == 1:
            malus_flucht = True

    if malus_muede == True and malus_flucht == True:
        malus_gesamt = 2
        print("Die englischen Einheiten sind müde und auf der Flucht. Malus: 2.")
    elif malus_muede == True and malus_flucht == False:
        malus_gesamt = 1
        print("Die englischen Einheiten sind müde. Malus: 1.")
    elif malus_muede == False and malus_flucht == True:
        malus_gesamt = 1
        print("Die englischen Einheiten sind auf der Flucht. Malus: 1.")
    else:
        malus_gesamt = 0

    return malus_gesamt


def ratio(engTruppen, franzTruppen, attacker, attacker_bonus, defender_bonus):
    """Funktion zur Ausgabe eines Verhältnisses im Format 'Angreifer:Verteidiger'"""
    staerke_E = 0
    staerke_F = 0
    for t in engTruppen:
        staerke_E = int(staerke_E + strength(t, "E"))

    for t in franzTruppen:
        staerke_F = int(staerke_F + strength(t, "F"))

    print("Es stehen sich " + str(staerke_E) + " englische und " + str(
        staerke_F) + " französische Männer gegenüber.")

    if attacker == "e":
        print(f"Angreifer ist England, Verteidiger ist Frankreich.")
    else:
        print(f"Angreifer ist Frankreich, Verteidiger ist England.")

    print(f'Der Angreifer hat einen manuell eingegebenen Bonus von {attacker_bonus}, der Verteidiger einen Bonus von {defender_bonus}.')

    if attacker == "e":
        zahl1 = staerke_E
        zahl2 = staerke_F
    elif attacker == "f":
        zahl1 = staerke_F
        zahl2 = staerke_E

    a, v = numerical_ratio(zahl1, zahl2)
    artillery_E, artillery_F = artillery_check(engTruppen, franzTruppen)
    bonus_entrenched_E = entrenched(engTruppen,"E")
    bonus_entrenched_F = entrenched(franzTruppen, "F")
    xp_bonus, xp_winner = experience_check(engTruppen, franzTruppen)
    if xp_winner == "e":
        xp_bonus_E = xp_bonus
        xp_bonus_F = 0
    elif xp_winner == "f":
        xp_bonus_F = xp_bonus
        xp_bonus_E = 0
    else:
        xp_bonus_F = 0
        xp_bonus_E = 0

    if attacker == "e":
        malus_check_a = normalize_malus_E(engTruppen)
        malus_check_v = normalize_malus_F(franzTruppen)
        artillery_A = artillery_E
        artillery_V = artillery_F
        xp_bonus_A = xp_bonus_E
        xp_bonus_V = xp_bonus_F
        entrenched_bonus_A = bonus_entrenched_E
        entrenched_bonus_V = bonus_entrenched_F
    elif attacker == "f":
        malus_check_a = normalize_malus_F(franzTruppen)
        malus_check_v = normalize_malus_E(engTruppen)
        artillery_A = artillery_F
        artillery_V = artillery_E
        xp_bonus_A = xp_bonus_F
        xp_bonus_V = xp_bonus_E
        entrenched_bonus_A = bonus_entrenched_F
        entrenched_bonus_V = bonus_entrenched_E

    a -= malus_check_a
    v -= malus_check_v
    a += artillery_A
    v += artillery_V
    a += xp_bonus_A
    v += xp_bonus_V
    a += attacker_bonus
    v += defender_bonus
    a += entrenched_bonus_A
    v += entrenched_bonus_V

    a, v = numerical_ratio(a, v)
    ratio = str(a) + ":" + str(v)
    return ratio


def numerical_ratio(zahl1, zahl2):
    """Funktion zur Berechnung des auf Ganzzahlen gerundeten Verhältnisses zweier Zahlen"""
    if zahl1 <= 0:
        add = 1 + abs(zahl1)
        zahl1 += add
        zahl2 += add
    if zahl2 <= 0:
        add = 1 + abs(zahl2)
        zahl1 += add
        zahl2 += add

    gcd = math.gcd(zahl1, zahl2)
    one = zahl1 / gcd
    two = zahl2 / gcd

    result = one / two

    if result > 5:
        result = 5

    if result > 0.62 and result < 0.72:
        a = 2
        v = 3
        # ratio = "2:3"
    elif result > 1.45 and result < 1.55:
        a = 3
        v = 2
        # ratio = "3:2"
    elif result >= 1:
        a = round(result)
        v = 1
        # ratio = str(round(result)) + ":1"

    elif result <= 1:
        result = two / one
        if result > 5:
            result = 5
        a = 1
        v = round(result)
        # ratio = "1:" + str(round(result))

    return a, v


# W Ü R F E L N

def roll_dice ():
    """Funktion zur Ausgabe eines Zufallswerts zwischen 1 und 6"""
    dice = random.randint(1, 6)
    uni_dices = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    print(f'Würfelergebnis: {dice} {uni_dices[dice]}')
    return dice


def check_results(ratio, dice):
    """Funktion zum Abgleich des Verhältnisses und des Würfelergebnisses mit der Tabelle zum Gefechtsausgang"""
    tab = pd.read_csv(path_to_data() + "/kampfergebnis.csv", sep=";")
    index = tab[tab['Verhältnis'] == ratio].index.values.astype(int)[0]
    result_a = tab.at[index, str(dice) + "A"].lower()
    result_v = tab.at[index, str(dice) + "V"].lower()
    if result_a == "würfeln":
        print("=> Erneut würfeln: ", end="")
        result_a, result_v = check_results(ratio, roll_dice())
    return result_a, result_v


def take_damage(name, result, df, side, ort):
    """Funktion zur Eintragung der Kampfergebnisse in die Dataframes"""
    global vernichtet
    damage = pd.read_csv(path_to_data() + "/zustaende.csv", sep=";", index_col="result").to_dict()
    new_strength = int(round(damage["mult"][result] * df.at[name, "staerke_aktuell"]))
    df.at[name, "staerke_aktuell"] = new_strength
    df.loc[name, "standort_aktuell"] = ort

    if df.at[name, "staerke_aktuell"] <= 0:
        vernichtet.append(name)
    if result == "flucht" or result == "muede":
        df.at[name, result] = damage["dauer"][result]

    message = "Zustand: " + str(result) + ", neue Stärke: " + str(new_strength)
    report_entry(side, "kampf", str(name), message)
    return df


# (B) T R U P P E N V E R W A L T U N G

def remove_destroyed():
    """Funktion zur Ausgabe der Truppenliste unter Abzug der vernichteten Truppen"""
    troops_E_show = list(troops_E)
    troops_F_show = list(troops_F)

    for vernichtete_truppe in vernichtet:
        if vernichtete_truppe in troops_E_show:
            troops_E_show.remove(vernichtete_truppe)
        if vernichtete_truppe in troops_F_show:
            troops_F_show.remove(vernichtete_truppe)
    return troops_E_show, troops_F_show


def lookout(name, side, new_location, see):
    """Funktion zur Eintragung eines Spähmanövers in die Dataframes"""
    location_old = side._get_value(name, "standort_letzteRunde")
    side.loc[name, "standort_aktuell"] = new_location


def dig_in(name, side, duration):
    """Funktion zur Eintragung der Befestigung einer Stellung in die Dataframes"""
    schon_eingegraben  = side._get_value(name, "eingegraben")
    if schon_eingegraben != 0:
        print("Die Einheit ist bereits eingegraben. Sie kann kein zweites Mal eingegraben werden.")
    else:
        location_old = side._get_value(name, "standort_letzteRunde")
        print("Standort: " + str(location_old) + "\n")
        side.at[name, "eingegraben"] = -duration
        print("Die Einheit wird für " + str(duration) + " Runden beschäftigt sein. Dies macht "
                                                    "sie anfälliger für Überraschungangriffe." + "\n"+ "\n")


def dig_out(name, side, duration):
    """Funktion zur Eintragung des Abreißens einer Stellung in die Dataframes"""
    duration = 100 + duration
    schon_eingegraben  = side._get_value(name, "eingegraben")
    if schon_eingegraben != 0:
        side.at[name, "eingegraben"] = duration
        print("Die Einheit wird für " + str(duration - 100) + " Runden beschäftigt sein. Dies macht "
                                                    "sie anfälliger für Überraschungangriffe." + "\n"+ "\n")
    else:
        print("Eine Einheit muss eingegraben sein, bevor sie ausgegraben werden kann.")


def movement(name, side, location_new):
    """Funktion zur Eintragung von Truppenbewegungen in die Dataframes"""
    location_old = side._get_value(name, "standort_letzteRunde")
    print("Die Einheit befindet sich momentan hier: " + str(location_old))
    print("Nach Bewegung der Einheit ist dies nun der neue Standort: "+ location_new)
    side.loc[name, "standort_aktuell"] = location_new


# (C) T A B E L L E N  A N Z E I G E N
# s. Funktion show_dataframes()


# (D) R U N D E  B E E N D E N

def round_update (df):
    """Funktion zur Aktualisierung der Werte in den Dataframes bei Rundenende"""
    for name,row in df.iterrows():
        current_value_flucht = df._get_value(name, "flucht")
        if current_value_flucht > 0:
            df.at[name, "flucht"] -= 1
        current_value_muede = df._get_value(name, "muede")
        if current_value_muede > 0:
            df.at[name, "muede"] -= 1
        entrenched = df._get_value(name, "eingegraben")
        if entrenched == -1:
            print(name + " ist ab sofort eingegraben.")
            new_entrenched = 99
            df._set_value(name, "eingegraben", new_entrenched)
        elif entrenched < 0:
            new_entrenched = entrenched + 1
            df._set_value(name, "eingegraben", new_entrenched)
            print(name + " gräbt sich gerade ein.")
        elif entrenched > 0 and entrenched < 100:
            print(name + " ist eingegraben.")
        elif entrenched > 100:
            new_entrenched = entrenched - 1
            df._set_value(name, "eingegraben", new_entrenched)
            print(name + "gräbt sich gerade aus.")
        elif entrenched == 100:
            print(name + "hat sich erfolgreich ausgegraben. ")
            new_entrenched = 0
            df._set_value(name, "eingegraben", new_entrenched)

        df["standort_letzteRunde"] = df["standort_aktuell"]
        #?? was passiert bei null?
    return df


# 6) E R G E B N I S P R O T O K O L L I E R U N G

def generateBattleResults(zeit, ort, attacker, truppen_a, truppen_v, verh, res_a, res_v):
    """Funktion zur Eintragung von Kampfergebnissen in results.csv"""
    string_a = ""
    string_v = ""
    for x in truppen_a:
        string_a += str(x) + ', '
    for y in truppen_v:
        string_v += str(y) + ', '

    res_ges = "Angreifer: " + res_a + ", " + "Verteidiger: " + res_v

    new_row = {'Zeitpunkt': zeit, 'Ort': ort, 'Angreifer': attacker.upper(), 'Truppen_Angreifer': string_a,
               'Truppen_Verteidiger': string_v, 'Verhältnis': verh, 'Resultat': res_ges}

    global results_csv
    results_csv = results_csv.append(new_row, ignore_index=True)
    results_csv.to_csv(path_to_results() + "/Results.csv", sep=";", index=False)


def report_entry (side, type, unit, message):
    """Funktion zur Eintragung einzelner Ereignisse in die Rundenberichte"""
    path = path_to_results() + "/report_" + side.upper() + "_round_" + str(runde) + ".txt"
    with open(path, 'a') as report:
        if type == "bewegung":
            report.write(unit+"\n"+"\t"+"Bewegung: "+message+"\n\n")
        elif type == "eingraben":
            report.write(unit+"\n"+"\t"+"gräbt sich ein für: "+message+" Runden."+"\n\n")
        elif type == "ausgraben":
            report.write(unit + "\n" + "\t" + "gräbt sich aus für: " + message + " Runden." + "\n\n")
        elif type == "spähen":
            report.write(unit+"\n"+"\t"+"Die Einheit hat beim Spähen Folgendes gesehen: "+message+"\n\n")
        elif type == "kampf":
            report.write(unit+"\n"+"\t"+"war in einen Kampf involviert. Die Folgen sind: "+message+"\n\n")


def save_files():
    """Funktion zum Abspeichern aller Simulationsdaten als Dictionary via Pickle"""
    dictionary ={}
    dictionary["zeit"] = zeit
    dictionary["startzeit"] = startzeit
    dictionary["runde"] = runde
    dictionary["england_df"] = england_df
    dictionary["frankreich_df"] = frankreich_df
    dictionary["vernichtet"] = vernichtet
    pickle.dump(dictionary, open(path_to_results() + "/previous_rounds.pkl", "wb"))


if __name__ == "__main__":
    main()