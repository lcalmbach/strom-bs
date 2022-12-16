import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import const

MONTHS_REV_DICT = {'Jan':1, 'Feb':2, 'Mrz':3, 'Apr':4, 'Mai':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9,'Okt':10,'Nov':11,'Dez':12}

def line_chart(df, settings):
    title = settings['title'] if 'title' in settings else ''
    if 'x_dt' not in settings: settings['x_dt'] = 'Q'
    if 'y_dt' not in settings: settings['y_dt'] = 'Q'
    if 'x_labels' in settings:
        x_axis = alt.Axis(values=settings['x_labels'])
    else:
        x_axis = alt.Axis()
    if 'x_title' not in settings:
        settings['x_title'] = ''
    if 'y_title' not in settings:
        settings['y_title'] = ''
    chart = alt.Chart(df).mark_line(width=2, clip=True).encode(
        x=alt.X(f"{settings['x']}:{settings['x_dt']}", title = settings['x_title'], axis=x_axis),
        y=alt.Y(f"{settings['y']}:{settings['y_dt']}", title = settings['y_title']),
        color = alt.Color(f"{settings['color']}",
                    scale=alt.Scale(scheme=alt.SchemeParams(name='rainbow'))),
        tooltip=settings['tooltip']
    )
    
    plot = chart.properties(width=settings['width'], height=settings['height'], title=title)
    st.altair_chart(plot)


def scatter_plot(df, settings):
    title = settings['title'] if 'title' in settings else ''
    if 'x_labels' in settings:
        x_axis = alt.Axis(values=settings['x_labels'])
    else:
        x_axis = alt.Axis()
    if 'x_title' not in settings:
        settings['x_title'] = ''
    if 'y_title' not in settings:
        settings['y_title'] = ''
    
    chart = alt.Chart(df).mark_circle(size=60, clip=True).encode(
        x=alt.X(f"{settings['x']}:Q", title = settings['x_title'], axis=x_axis),
        y=alt.Y(f"{settings['y']}:Q", title = settings['y_title'], scale=alt.Scale(domain=settings['y_domain'])),
        color = alt.Color(f"{settings['color']}",
                    scale=alt.Scale(scheme=alt.SchemeParams(name='rainbow')),
                    sort = list(const.MONTH_DICT.values())),
        tooltip=settings['tooltip']
    )

    line = alt.Chart(df).mark_line(
    color='red',
    size=3
    ).transform_window(
        rolling_mean=f"mean({settings['y']})",
        frame=[-60, 60]
    ).encode(
        x=settings['x'],
        y='rolling_mean:Q'
    )
    
    plot = chart.properties(width=settings['width'], height=settings['height'], title=title)
    st.altair_chart(plot)


def barchart(df, settings):
    title = settings['title'] if 'title' in settings else ''
    """
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f'year:N', axis=alt.Axis(title='', labelAngle=90)),
        y=alt.Y(f'stromverbrauch_kwh:Q', title=settings['y_title'], axis=alt.Axis(grid=False)),
        column = alt.Column('month:N',title=""),
        color='year:N',
        tooltip=settings['tooltip']
        ).configure_view(
            stroke=None,
        )
    """
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('sum(stromverbrauch_kwh):Q', title=settings['x_title']),
        y=alt.Y('year:O', title=settings['y_title']),
        color='year:N',
        row=alt.Row('month:N', sort=list(MONTHS_REV_DICT.keys()) ),
        tooltip=settings['tooltip']
    )

    plot = chart.properties(width=settings['width'], height=settings['height'], title=title)
    st.altair_chart(plot)
