##################
### EDF Prices ###
##################

# Price of subscription, per month
monthly_subscription = 7.77
monthly_subscription_net = monthly_subscription * 1.05

# Taxes
tcfe_khw_price = 0.00957
tcfe_khw_price_net = tcfe_khw_price * 1.2

cspe_kwh_price = 0.02250
cspe_kwh_price_net = cspe_kwh_price * 1.2

cta_price = 16.29
cta_price_net = cta_price * 1.05
montly_cta_price_net = cta_price_net/12

# kWh prices ("Heures creuses" and "Heures pleines")
kwh_hc_price = 0.0738
kwh_hc_price_net = kwh_hc_price * 1.2

kwh_hp_price = 0.0979
kwh_hp_price_net = kwh_hp_price * 1.2

estimated_month_price = 120.0

#######################
### InfluxDB config ###
#######################

IP = "localhost"                # The IP of the machine hosting your influxdb instance
DB_HIGH_RENT = "edf_instant_db" # The database to write to, has to exist
DB_LOW_RENT  = "edf_db"         # The database to write to, has to exist
USER = "admin"                  # The influxdb user to authenticate with
PASSWORD = "admin"              # The password of that user

########################
### InfluxDB metrics ###
########################

month_eur = ["jan_eur" ,"feb_eur" ,"mar_eur" ,"apr_eur" ,"may_eur" ,"jun_eur" ,"jul_eur" ,"aug_eur" ,"sep_eur" ,"oct_eur" ,"nov_eur" ,"dec_eur"]

####################
### Data parsing ###
####################

hchc_data_length = 9
hchp_data_length = 9
iinst_data_length = 3