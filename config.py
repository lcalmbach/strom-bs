url_daily_temperature = "https://data.bs.ch/api/v2/catalog/datasets/100051/records?limit=-1&offset=0&timezone=UTC&select=year(datum_zeit)%20as%20jahr,month(datum_zeit)%20as%20monat,day(datum_zeit)%20as%20tag,avg(temp_c)%20as%20avg_temp_c&group_by=year(datum_zeit),month(datum_zeit),day(datum_zeit)&where=datum_zeit%20>%20date'2021-12-31'"
# &where=datum_zeit%20%3E%20date%272022-12-10%27

MONTH_DICT = {1:'Jan',2:'Feb',3:'Mrz',
    4:'Apr',5:'Mai',6:'Jun',
    7:'Jul', 8:'Aug', 9:'Sep', 
    10:'Okt', 11:'Nov', 12:'Dez'}