#!/usr/bin/python
# coding: utf-8

from config import *
import datetime
import serial
import pickle
import requests
import time

### Lecture des donnees series fournies par le compteur EDF
def readSerialData():
    ser = serial.Serial(port='/dev/ttyUSB0', baudrate=1200, parity=serial.PARITY_EVEN, bytesize=serial.SEVENBITS, timeout=1)
    edf_string = ser.read(size=200)
    current_kwh_hc = readOneSerialData(edf_string, "HCHC", hchc_data_length)
    current_kwh_hc = float(current_kwh_hc)/1000
    current_kwh_hp = readOneSerialData(edf_string, "HCHP", hchp_data_length)
    current_kwh_hp = float(current_kwh_hp)/1000
    instant_intensity = readOneSerialData(edf_string, "IINST", iinst_data_length)
    period_is_hp = pricePeriodIsHp(edf_string, "PTEC")
    return current_kwh_hc, current_kwh_hp, instant_intensity, period_is_hp

def readOneSerialData(serial_string, string_to_find, data_length):
    index = serial_string.find(string_to_find)
    data_line = serial_string[index : index+data_length+len(string_to_find)+3]
    return int(data_line[len(string_to_find)+1 : len(string_to_find)+data_length+2])

def pricePeriodIsHp(serial_string, string_to_find):
    index = serial_string.find(string_to_find)
    data_line = serial_string[index : index+9]
    if data_line.find("HP") != -1:
        return True
    else:
        return False

### Calcul de la puissance instantannee en W (consommation approximative )
def currentConsumptionW( ampere_val ):
    return ampere_val*230

### Calcule un prix en euros TTC en fonction d'une consommation electrique (en kWh)
def kwhToEurosHc ( measure ):
    return (measure * (kwh_hc_price_net + tcfe_khw_price_net + cspe_kwh_price_net))
def kwhToEurosHp ( measure ):
    return (measure * (kwh_hp_price_net + tcfe_khw_price_net + cspe_kwh_price_net))

### Conversion d'une consommation en EUR en un pourcentage par rapport au prix estime par EDF
def convertConsumptionToPercentage ( total_month_consumption ):
    return (total_month_consumption * 100 / estimated_month_price)

### Envoi d'une metrique dans la base de donnees InfluxDB
def pushMetricToDatabase ( metric_name, metric_value, high_retention_policy ):
    metric = "%s value=%s" %(metric_name, metric_value)
    if high_retention_policy:
        r = requests.post("http://%s:8086/write?db=%s" %(IP, DB_HIGH_RENT), auth=(USER, PASSWORD), data=metric)
    else:
        r = requests.post("http://%s:8086/write?db=%s" %(IP, DB_LOW_RENT), auth=(USER, PASSWORD), data=metric)
    if r.status_code != 204:
        return False
    else:
        return True

def waitOneMinute ():
    date = datetime.datetime.now()
    ref_min = date.minute
    new_min = date.minute
    while (ref_min == new_min):
        date = datetime.datetime.now()
        new_min = date.minute

def dateToIndex (date, wanted_month):
    index = date-2
    if index == -1:
        return 11
    else:
        return index


while (True):
    waitOneMinute()
    date = datetime.datetime.now()
    edf = readSerialData()
    current_kwh_hc = edf[0]
    current_kwh_hp = edf[1]
    instant_intensity = edf[2]
    period_is_hp = edf[3]

    ### Toutes les minutes, on met a jour les donnees suivantes dans la base de donnees InfluxDB :
    ###     - instant_watt_hp : puissance instantannee en W si heures pleines
    ###     - instant_watt_hc : puissance instantannee en W si heures creuses
    if period_is_hp:
        pushMetricToDatabase("instant_watt_hp", currentConsumptionW(instant_intensity), True)
        pushMetricToDatabase("instant_watt_hc", 0, True)
    else:
        pushMetricToDatabase("instant_watt_hp", 0, True)
        pushMetricToDatabase("instant_watt_hc", currentConsumptionW(instant_intensity), True)

    ### Debut du mois, on met a jour les donnees suivantes dans la base de donnees InfluxDB :
    ###     - current_month_percent : pourcentage consomme en euros par rapport a la facture previsionnelle prevue par EDF
    ###     - month_eur : somme totale d'euros consommes pour le mois en cours
    ### en effet, si la consommation est pour l'instant nulle, on ajoute un "offset" qui correspond au montant de l'abonnement EDF
    if ( date.day == 1 and date.hour == 0 and date.minute == 1):
        stored_measures = pickle.load( open( "data.pickle", "rb" ) )
        pushMetricToDatabase(month_eur[dateToIndex(date.month)], stored_measures["monthly_eur"], False)
        stored_measures["monthly_eur"] = montly_cta_price_net + monthly_subscription_net
        pickle.dump( stored_measures, open( "data.pickle", "wb" ) )

    ### Fin de la journee, on met a jour les donnees suivantes dans la base de donnees InfluxDB :
    ###     - daily_eur : quantite d'electricite consommee dans la journee en euros
    ###     - daily_kwh : quantite d'electricite consommee dans la journee en kWh
    ###     - current_month_percent : pourcentage consomme en euros par rapport a la facture previsionnelle prevue par EDF
    ###     - month_eur : somme totale d'euros consommes pour le mois en cours
    if ( date.hour == 23 and date.minute == 59):
        stored_measures = pickle.load( open( "data.pickle", "rb" ) )        
        # On calclue la consommation journaliere
        day_kwh_hc = current_kwh_hc - stored_measures["last_day_kwh_hc"]
        day_kwh_hp = current_kwh_hp - stored_measures["last_day_kwh_hp"]
        # On converti la consommation electique en consommation pecuniere
        day_eur_hc = kwhToEurosHc(day_kwh_hc)
        day_eur_hp = kwhToEurosHp(day_kwh_hp)
        # On somme la consommation journaliere
        daily_eur = day_eur_hc + day_eur_hp
        daily_kwh = day_kwh_hc + day_kwh_hp
        # On met a jour les consommations stockees pour le calcul du lendemain
        stored_measures["last_day_kwh_hc"] = current_kwh_hc
        stored_measures["last_day_kwh_hp"] = current_kwh_hp
        # On ajoute la consommation journaliere (en euros) a la consommation mensuelle totale
        stored_measures["monthly_eur"] += daily_eur
        # On pousse les metriques journalieres dans la base de donnees InfluxDB
        pushMetricToDatabase('daily_eur', daily_eur, False)
        pushMetricToDatabase('daily_kwh', daily_kwh, False)
        pushMetricToDatabase('current_month_percent', convertConsumptionToPercentage(stored_measures["monthly_eur"]), False)
        pickle.dump( stored_measures, open( "data.pickle", "wb" ) )