#!/usr/bin/python

# Script a utiliser pour modifier le dictionnaire stocke dans le fichier "data.pickle"

import pickle

stored_measures = { \
	"last_day_kwh_hc": 0.0, \
	"last_day_kwh_hp": 0.0, \
	"monthly_eur": 0.0 \
	}

pickle.dump( stored_measures, open( "data.pickle", "wb" ) )