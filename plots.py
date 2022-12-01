import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime


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

