from datetime import date

url_daily_temperature = "https://data.bs.ch/api/v2/catalog/datasets/100051/records?limit=-1&offset=0&timezone=UTC&select=year(datum_zeit)%20as%20jahr,month(datum_zeit)%20as%20monat,day(datum_zeit)%20as%20tag,avg(temp_c)%20as%20avg_temp_c&group_by=year(datum_zeit),month(datum_zeit),day(datum_zeit)&where=datum_zeit%20>%20date'2021-12-31'"
SOURCE_FILE = './100233.csv'
PARQUET_FILE = SOURCE_FILE.replace('csv', 'gzip')
#SOURCE_URL = 'https://data.bs.ch/explore/dataset/100233'
SOURCE_URL = 'https://data.bs.ch/explore/dataset/100233/download/?format=csv&timezone=Europe/Zurich&lang=de&use_labels_for_header=false&csv_separator=%3B'
GIT_REPO = 'https://github.com/lcalmbach/strom-bs'


def_options_days = (1, 365)
def_options_hours = (0, 23)
def_options_weeks = (1, 53)
def_options_months = (1,12)
CURRENT_YEAR = date.today().year
FIRST_YEAR = 2012

MONTH_DICT = {1:'Jan',2:'Feb',3:'Mrz',
    4:'Apr',5:'Mai',6:'Jun',
    7:'Jul', 8:'Aug', 9:'Sep', 
    10:'Okt', 11:'Nov', 12:'Dez'}

url_new_el_data = "https://data.bs.ch/api/v2/catalog/datasets/100233/exports/csv/?limit=-1&offset=0&timezone=UTC&where=timestamp_interval_start>date'2022-12-12"
url_last_el_rec = "https://data.bs.ch/api/v2/catalog/datasets/100233/exports/csv?limit=1&timezone=UTC&select=timestamp_interval_start&offset=0&order_by=timestamp_interval_start%20DESC"
url_recent_records = "https://data.bs.ch/api/v2/catalog/datasets/100233/exports/csv?limit=-1&timezone=UTC&where=timestamp_interval_start>date'2022-12-10'"