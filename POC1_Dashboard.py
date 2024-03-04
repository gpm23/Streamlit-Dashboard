import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import sys


st.title("Putting the POC1 charts in Streamlit")

st.write("Velo AI and Pitt Capstone Team")

def make_gpsmap(lat, lon, lat_list, lon_list):

    fig = px.scatter_mapbox(lat=lat_list, lon=lon_list,
                            center=dict(lat=lat, lon=lon),
                            mapbox_style='carto-positron',
                            zoom=16, width=600, height=600)
    fig.add_trace(px.line_mapbox(lat=lat_list, lon=lon_list).data[0])
    fig.add_trace(px.scatter_mapbox(lat=[lat], lon=[lon],
                                    size=[10], color=['red']).data[0])
    return fig
def make_gpsmap_from_row(row, df):
    df_filter = df[df['sourcefile'] == row['sourcefile']]
    t1 = row['timestamp'] - 100
    t2 = row['timestamp'] + 100
    df_filter = df_filter[(df_filter['timestamp'] >= t1) & (df_filter['timestamp'] <= t2)]
    lat_list = df_filter['latitude'].values
    lon_list = df_filter['longitude'].values
    lat = row['latitude']
    lon = row['longitude']

    fig = make_gpsmap(lat, lon, lat_list, lon_list)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(showlegend=False)
    return fig
#Import the data
df = pd.read_pickle("sample_df.pkl")

scale = 1000000 # unitless
df['associated_ride'].nunique() # 2 rides pre and post
df2 = df[df['associated_ride'] == 'Ride2']
df2pre = df2[df2['pre_or_post'] == 'pre']
df2 = df2[df2['pre_or_post'] == 'post']

df1 = df[df['associated_ride'] == 'Ride1']
df1 = df1[df1['pre_or_post'] == 'post']
df1pre = df1[df1['pre_or_post'] == 'pre']

df1['dt'] = df1['gps_timestamp_adjusted'].diff()
df1['rel_time'] = np.arange(len(df1))
df1['lat_diff'] = df1['latitude'].diff()
df1['long_diff'] = df1['longitude'].diff()
df1['speed'] = ((((df1['lat_diff'] / df1['dt']) ** 2.0) + ((df1['long_diff'] / df1['dt']) ** 2.0)) ** .5) * scale

df1['v_lat'] = df[df['behavior'].isin(['OVERTAKING', 'APPROACHING', 'FOLLOWING'])]['latitude']
df1['v_long'] = df[df['behavior'].isin(['OVERTAKING', 'APPROACHING', 'FOLLOWING'])]['longitude']


#Plot 1: Scatter plot of lat/lon locations where vehicles were observed
st.header("Plot 1: Scatter plot of lat/lon locations where vehicles were observed")
st.write(make_gpsmap(df1['v_lat'].dropna().iloc[0], df1['v_long'].dropna().iloc[0], df1['v_lat'].dropna().values, df1['v_long'].dropna().values))

st.write(px.scatter(df1, x=df1['v_lat'], y=df1['v_long']))

#Plot 2: Time sereies plot of speed of bicycle over time
st.header("Plot 2: Time sereies plot of speed of bicycle over time")
fig = go.Figure()
fig.add_trace(go.Line(
    x=df1['gps_timestamp_adjusted'][:500],
    y=df1['speed'][:500],
))
fig.update_layout(
    xaxis_title="Time",
    yaxis_title="Speed",
    title="Biker Speed over Time"
)
st.write(fig)

#Plot 3: Histogram of bikes speeds
st.header("Plot 3: Histogram of bikes speeds")
st.write(px.histogram(df1, 'speed'))
