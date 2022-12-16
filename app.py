import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from os.path import exists
from datetime import datetime, timedelta, date
from utilities import load_css
import requests
import io
import pytz
import numpy as np

import plots
from const import *
import text

__version__ = '0.0.4'
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2022-12-16'
my_name = 'Verbrauch Elektrizität im Kanton Basel-Stadt'
my_kuerzel = "ElV-bs"

utc=pytz.UTC

def init():
    st.set_page_config(  # Alternate names: setup_page, page, layout
        initial_sidebar_state = "auto", 
        page_title = 'e-Verbrauch-bs', 
        page_icon = '⚡',
    )
    load_css()

def get_info(last_date):
    text = f"""<div style="background-color:#34282C; padding: 10px;border-radius: 15px; border:solid 1px white;">
    <small>App von <a href="mailto:{__author_email__}">{__author__}</a><br>
    Version: {__version__} ({VERSION_DATE})<br>
    Quelle: <a href="{SOURCE_URL}">OGD Basel-Stadt</a><br>
    Daten bis: {last_date.strftime('%d.%m.%Y %H:%M')}
    <br><a href="{GIT_REPO}">git-repo</a></small></div>
    """
    return text

@st.experimental_memo(ttl=6*3600, max_entries=3)
def get_data():
    def last_recort_timestamp():
        response = requests.get(url_last_el_rec)
        df = pd.read_csv(io.StringIO(response.text), sep=";")
        df['timestamp_interval_start'] = pd.to_datetime(df['timestamp_interval_start'])
        ts = df.iloc[0]['timestamp_interval_start']
        return ts

    def get_records(df, ts):
        url = url_recent_records.format(ts.date())
        response = requests.get(url)
        df = pd.read_csv(io.StringIO(response.text), sep=";")
        return df

    def get_recent_data(df):
        max_time_local = df['timestamp_interval_start'].max()
        max_time_local = pd.Timestamp(max_time_local.year, max_time_local.month, max_time_local.day, max_time_local.hour, max_time_local.minute)
        max_time_local = utc.localize(max_time_local)
        max_time_remote = last_recort_timestamp().date()
        if max_time_local < max_time_remote: # (max_time_remote - timedelta(days = 1)):
            # get the new records starting on the start of the day
            df_new_records = get_records(df, max_time_local)
            # remove existing records from first day where records were missing
            df = df[df['timestamp_interval_start'] < pd.Timestamp(max_time_remote).tz_localize('utc')]
            # concat both
            df = pd.concat([df, df_new_records], ignore_index=True)
            df['timestamp_interval_start'] = pd.to_datetime(df['timestamp_interval_start'])
        return df

    def add_aggregation_codes(df):
        df['year'] = df['timestamp_interval_start'].dt.year
        df['day'] = 15
        df['month'] = 7
        df['year_date'] = pd.to_datetime(df[['year','month','day']])
        df['hour'] = df['timestamp_interval_start'].dt.hour
        df['minute'] = df['timestamp_interval_start'].dt.minute
        df['date'] = pd.to_datetime(df['timestamp_interval_start']).dt.date
        df['date'] = pd.to_datetime(df['date'])
        df['week'] = df['timestamp_interval_start'].dt.isocalendar().week
        df['month'] = df['timestamp_interval_start'].dt.month
        df['year'] = df['timestamp_interval_start'].dt.year
        df['week_date'] = df['date'] - pd.offsets.Week(weekday=6)
        df['month_date'] = pd.to_datetime(df[['year','month','day']])
        df['day_in_month'] = pd.to_datetime(df['timestamp_interval_start']).dt.day
        df['day'] = df['timestamp_interval_start'].dt.day
        df['hour_date'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
        df['day'] = df['timestamp_interval_start'].dt.dayofyear
        df['zeit'] = df['timestamp_interval_start'].dt.strftime('%H:%M')
        df['day_of_week'] = df['timestamp_interval_start'].dt.dayofweek
        df['week_time'] = df['day_of_week'] + df['hour']/24 + df['timestamp_interval_start'].dt.minute / (24*60)
        df = df[df['year'] > 2011]
        return df

    if exists(PARQUET_FILE):
        df = pd.read_parquet(PARQUET_FILE)
        df = get_recent_data(df)
    else:
        df = pd.read_csv(SOURCE_FILE, sep=';')
        fields = ['timestamp_interval_start', 'stromverbrauch_kwh']
        df['timestamp_interval_start'] = pd.to_datetime(df['timestamp_interval_start'], utc=True, errors='coerce')
        df = df[fields]
        df.to_parquet(PARQUET_FILE, compression='gzip')
    
    df = add_aggregation_codes(df)
    df['stromverbrauch_kwh'] = df['stromverbrauch_kwh'] / 1e6
    # df = add_aggregation_codes(df)
    return df


def get_interval_dates(sel_days):
    base_date = datetime(CURRENT_YEAR, 1, 1)
    fmt = "%d.%m/%y"
    dat1 = base_date + timedelta(days=sel_days[0]-1)
    dat2 = base_date + timedelta(days=sel_days[1]-1)
    return f"{dat1.strftime(fmt)[:5]} - {dat2.strftime(fmt)[:5]}"


def consumption_year(df):
    def show_plot(df):
        settings = {'x': 'day', 'y':'cum_stromverbrauch_kwh', 'color':'year:O', 'tooltip':['year','day', 'cum_stromverbrauch_kwh', 'stromverbrauch_kwh'], 
                'width':800,'height':400, 'y_title': 'Kumulierter Verbrauch [GWh]', 'x_title': 'Tag im Jahr', 
                'title': "Kumulierter Verbrauch"}
        plots.line_chart(df, settings)
        # st.markdown(figure_text['year'][0])

        settings['y'] = 'stromverbrauch_kwh'
        settings['y_title'] = 'Verbrauch [MWh]'
        settings['title'] = "Tages-Verbrauch"
        plots.line_chart(df, settings)
        # st.markdown(figure_text['year'][1])

    def get_filtered_data(df):
        with st.sidebar.expander('🔎 Filter', expanded=True):
            sel_days = st.slider('Auswahl Tag im Jahr', min_value=1, max_value=max(def_options_days), value=def_options_days)
            st.markdown(get_interval_dates(sel_days))
            sel_years = st.multiselect('Auswahl Jahre', options=range(FIRST_YEAR,CURRENT_YEAR+1), help="keine Auswahl = alle Jahre")
        if sel_days != def_options_days:
            df = df[(df['day'] >= sel_days[0]) & (df['day'] <= sel_days[1])]
        if sel_years:
            df = df[df['year'].isin(sel_years)]
        return df

    df_year = get_filtered_data(df.copy())
    fields = ['year', 'day', 'stromverbrauch_kwh']
    agg_fields = ['year', 'day']
    df_year = df_year[fields].groupby(agg_fields).sum().reset_index()
    df_year['cum_stromverbrauch_kwh'] = df_year.groupby(['year'])['stromverbrauch_kwh'].cumsum()
    df_year['cum_stromverbrauch_kwh'] = df_year['cum_stromverbrauch_kwh'].round(1)
    df_year['stromverbrauch_kwh'] = df_year['stromverbrauch_kwh'].round(3)
    df_year = df_year[df_year['stromverbrauch_kwh'] > 2]
    show_plot(df_year)


def consumption_day(df):
    """
    Shows line-plot day of year versus cumulated consumption, one line per year

    Args:
        df (_type_): all consumptions
    """
    def show_plot(df):
        settings = {'x': 'zeit', 'x_dt': 'O', 'y':'stromverbrauch_kwh', 'color':'year:O', 'tooltip':['year','zeit', 'stromverbrauch_kwh'], 
                'width':800,'height':400, 'title': 'Tagesganglinie, mittlerer Viertelstunden-Verbrauch'}
        
        settings['x_labels'] = [f"{str(x).rjust(2, '0')}:00" for x in range(0,23+1)]
        plots.line_chart(df, settings)

    def get_filtered_data(df):
        with st.sidebar.expander('🔎 Filter', expanded=True):
            sel_days = st.slider('Auswahl Tag im Jahr', min_value=1, max_value=365, value=def_options_days)
            st.markdown(get_interval_dates(sel_days))
            
            sel_years = st.multiselect('Auswahl Jahre', options=range(FIRST_YEAR,CURRENT_YEAR+1), help="keine Auswahl = alle Jahre")
            if sel_days != def_options_days:
                df = df[(df['day'] >= sel_days[0]) & (df['day'] <= sel_days[1])]
        if sel_years:
            df = df[df['year'].isin(sel_years)]
        return df

    df_time = get_filtered_data(df.copy())
    df_time['stromverbrauch_kwh'] = df_time['stromverbrauch_kwh'] * 1000
    fields = ['year', 'zeit', 'stromverbrauch_kwh']
    agg_fields = ['year','zeit']
    df_time = df_time[fields].groupby(agg_fields).mean().reset_index()
    df_time['stromverbrauch_kwh'] = df_time['stromverbrauch_kwh'].round(1)
    show_plot(df_time)

@st.experimental_memo(ttl=6*3600, max_entries=3)
def get_temperature_data():
    url = url_daily_temperature
    response = requests.get(url)
    data = response.json()
    df = [{'Year': x['record']['fields']['year(datum_zeit)'], 
            'Month': x['record']['fields']['month(datum_zeit)'], 
            'Day': x['record']['fields']['day(datum_zeit)'], 
            'temperatur': x['record']['fields']['avg_temp_c']} for x in data['records']]
    df = pd.DataFrame(df)
    df[['Year', 'Month', 'Day']] = df[['Year', 'Month', 'Day']].astype(int)
    df['temperatur'] = df['temperatur'].astype(float)
    df['date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
    return df

def consumption_month(df):
    def show_barchart(df):
        settings = {'x': 'year', 'x_dt': 'N', 'y':'stromverbrauch_kwh', 'color':'year:O', 
            'tooltip':['year','month', 'stromverbrauch_kwh'], 
            'column':'month', 'col_dt': 'N', 'width':700,'height':200, 
            'title': 'Monatsvergleich, Stromverbrauch',
            'y_title': '',
            'x_title': 'Stromverbrauch(GWh)'}
        
        plots.barchart(df, settings)
    
    def show_timeseries(df):
        settings = {'x': 'month_date', 'x_dt': 'T', 'y':'stromverbrauch_kwh', 'color':'Wochentag:O', 
            'tooltip':['year','month', 'stromverbrauch_kwh'], 
            'column':'month', 'col_dt': 'N', 'width':800,'height':400, 
            'title': 'Zeitreihe Stromverbrauchs nach Monat',
            'y_title': 'Stromverbrauch (GWh)',
            'x_title': ''}
        plots.line_chart(df, settings)

    def get_filtered_data(df):
        with st.sidebar.expander('🔎 Filter', expanded=True):
            sel_months = st.slider('Auswahl Monate im Jahr', min_value=1, max_value=12, value=def_options_months)
            st.markdown(get_interval_dates(sel_months))
            
            sel_years = st.multiselect('Auswahl Jahre', options=range(FIRST_YEAR,CURRENT_YEAR+1), help="keine Auswahl = alle Jahre")
            if sel_months != def_options_days:
                df = df[(df['month'] >= sel_months[0]) & (df['month'] <= sel_months[1])]
        if sel_years:
            df = df[df['year'].isin(sel_years)]
        return df

    df_filtered = get_filtered_data(df.copy())
    fields = ['year', 'month', 'month_date', 'stromverbrauch_kwh']
    agg_fields = ['year','month', 'month_date']
    df_month = df_filtered[fields].groupby(agg_fields).sum().reset_index()
    df_month['stromverbrauch_kwh'] = df_month['stromverbrauch_kwh'].round(1)
    df_month['month'] = df_month['month'].replace(MONTH_DICT)
    show_barchart(df_month)
    
    df_filtered['weekday'] = ''
    df_filtered.loc[df_filtered['day_of_week'] > 4, 'Wochentag'] = 'Wochenende'
    df_filtered.loc[df_filtered['day_of_week'] < 5, 'Wochentag'] = 'Werktage'
    fields = ['year', 'month', 'month_date', 'Wochentag', 'stromverbrauch_kwh']
    agg_fields = ['year','month', 'month_date', 'Wochentag']

    df_month = df_filtered[fields].groupby(agg_fields).sum().reset_index()
    df_month['stromverbrauch_kwh'] = df_month['stromverbrauch_kwh'].round(1)
    df_month['month'] = df_month['month'].replace(MONTH_DICT)
    show_timeseries(df_month)


def consumption_week(df):
    """
    Shows line-plot day of week day versus average consumption, one line per year

    Args:
        df (_type_): all consumptions
    """
    def show_plot(df):
        settings = {'x': 'week_time', 'x_dt': 'O', 'y':'stromverbrauch_kwh', 'color':'year:O', 'tooltip':['year','week_time', 'stromverbrauch_kwh'], 
                'width':800,'height':400, 'title': 'Wochenganglinie, mittlerer Viertelstunden-Verbrauch', 'x_title': 'Wochentag',
                'y_title': 'Verbrauch [MWh]'}
        
        # settings['x_labels'] = {0: 'So',1:'Mon',2:'Di',3:'Mi',4:'Do',5:'Fr',6:'Sa'}
        # settings['x_labels'] = ['Mon','Di','Mi','Do','Fr','Sa','So']
        settings['x_labels'] = [0,1,2,3,4,5,6]
        plots.line_chart(df, settings)

    def get_filtered_data(df):
        with st.sidebar.expander('🔎 Filter', expanded=True):
            sel_weeks = st.slider('Auswahl Kalenderwochen', min_value=1, max_value=max(def_options_weeks), value=def_options_weeks)
            st.markdown(get_interval_dates(sel_weeks))
            
            sel_years = st.multiselect('Auswahl Jahre', options=range(FIRST_YEAR,CURRENT_YEAR+1), help="keine Auswahl = alle Jahre")
            if sel_weeks != def_options_weeks:
                df = df[(df['week'] >= sel_weeks[0]) & (df['week'] <= sel_weeks[1])]
        if sel_years:
            df = df[df['year'].isin(sel_years)]
        return df

    df_time = get_filtered_data(df.copy())
    df_time['stromverbrauch_kwh'] = df_time['stromverbrauch_kwh'] * 1000
    fields = ['year', 'week_time', 'stromverbrauch_kwh']
    agg_fields = ['year','week_time']
    df_time = df_time[fields].groupby(agg_fields).mean().reset_index()
    df_time['stromverbrauch_kwh'] = df_time['stromverbrauch_kwh'].round(1)
    show_plot(df_time)

def comparison_temp(df_consumption:pd.DataFrame):
    def show_plot(df, title):
        settings = {'x': 'temperatur', 'y':'stromverbrauch_kwh', 'color':'Monat:O', 'tooltip':['date', 'stromverbrauch_kwh', 'temperatur'], 
                'width':800,'height':400, 'title': title,
                'x_title': 'Temperatur °C', 'y_title': 'Verbrauch [MWh]', 'y_domain': [2000, 4000]}
        
        plots.scatter_plot(df, settings)

    df_temp = get_temperature_data()
    fields = ['date', 'stromverbrauch_kwh']
    agg_fields = ['date']
    df_consumption = df_consumption[fields].groupby(agg_fields).sum().reset_index()
    df_consumption['stromverbrauch_kwh']=df_consumption['stromverbrauch_kwh']*1e3 #convert to MWh
    df = pd.merge(df_temp, df_consumption, on = "date", how = "inner")
    df['Monat'] = df['Month'].replace(MONTH_DICT)
    df = df.sort_values(by='date')
    df_week_day = df[df['date'].dt.weekday < 5]
    df_weekend_day = df[df['date'].dt.weekday > 4]
    title = 'Stromverbrauch in Funktion der mittleren Tagestemperatur im 2022, an Werktagen'
    show_plot(df_week_day, title)
    title = 'Stromverbrauch in Funktion der mittleren Tagestemperatur im 2022, an Wochenend-Tagen'
    st.markdown(text.temp_verbr_weekday_legend, unsafe_allow_html=True)
    show_plot(df_weekend_day, title)
    st.markdown(text.temp_verbr_weekend_legend, unsafe_allow_html=True)
    return df

def main():
    """
    main menu with 3 options: cum consumption year of day, mean daily consumption in week 
    and mean 1/4 consumption in day for selected period and years
    """
    init()
    df = get_data()
    st.markdown(f"### Verbrauch elektrische Energie des Kanton Basel-Stadt, seit {FIRST_YEAR}")
    st.sidebar.markdown("### ⚡ Verbrauch-bs")

    menu_options = ['Jahresverlauf', 'Montsvergleich', 'Wochenverbrauch', 'Tagesverlauf', 'Vergleich E-Verbrauch/Temp']
    with st.sidebar:
        menu_action = option_menu(None, menu_options, 
        icons=['calendar', 'calendar', 'calendar', 'clock', 'thermometer'], 
        menu_icon="cast", default_index=0)

    if menu_action == menu_options[0]:
        consumption_year(df)
    elif menu_action == menu_options[1]:
        consumption_month(df)
    elif menu_action == menu_options[2]:
        consumption_week(df)
    elif menu_action == menu_options[3]:
        consumption_day(df)
    elif menu_action == menu_options[4]:
        comparison_temp(df)

    st.sidebar.markdown(get_info(df['timestamp_interval_start'].max()), unsafe_allow_html=True)

if __name__ == '__main__':
    main()



