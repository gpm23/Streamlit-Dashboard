import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import sys
import boto3
from io import BytesIO


#Connect to dashboard to AWS buckets
ACCESS_ID = os.environ.get('ACCESS_ID')
SECRET_KEY = os.environ.get('SECRET_KEY')
BUCKET_NAME = os.environ.get('BUCKET_NAME')

s3 = boto3.client('s3', aws_access_key_id=ACCESS_ID, aws_secret_access_key=SECRET_KEY)

#Import the data from AWS bucket
def load_data_from_s3(bucket_name, object_key):
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    data = response['Body'].read()
    df = pd.read_pickle(BytesIO(data))
    return df
#checking contents of bucket to make sure data is there
def list_objects_in_bucket(bucket_name):
    try:
        bucket_contents = s3.list_objects(Bucket=bucket_name)['Contents']
        for obj in bucket_contents:
            st.write(obj['date'])
    except Exception as e:
        print(e)

#Make a path to the dataset within bucket
object_key = 'sample_df.pkl'
df = load_data_from_s3(BUCKET_NAME, object_key)

print(df.head())

def make_gpsmap(lat, lon, lat_list, lon_list):

    fig = px.scatter_mapbox(lat=lat_list, lon=lon_list,
                            center=dict(lat=lat, lon=lon),
                            mapbox_style='carto-positron',
                            zoom=16, width=600, height=500)
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

#Make a path to the dataset within bucket
object_key = 'sample_df.pkl'
df = load_data_from_s3(BUCKET_NAME, object_key)

print(df.head())

list_objects_in_bucket(BUCKET_NAME)
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
graph1 = make_gpsmap(df1['v_lat'].dropna().iloc[0], df1['v_long'].dropna().iloc[0], df1['v_lat'].dropna().values, df1['v_long'].dropna().values)

#st.write(px.scatter(df1, x=df1['v_lat'], y=df1['v_long']))

#Plot 2: Time sereies plot of speed of bicycle over time

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
graph2 = fig

#Plot 3: Histogram of bikes speeds
graph3 = px.histogram(df1, 'speed')



#displays a video
def display_video(video_key):
    try:
        # Retrieve the content of the object from S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=video_key)
        content = response['Body'].read()
        st.video(content)  # Display the content (you may need to modify this based on the actual content type)
    except Exception as e:
        st.error(f"An error occurred: {e}")
#displays an image
def display_image(image_key):
    try:
        # Retrieve the content of the object from S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=image_key)
        content = response['Body'].read()
        st.image(content)  # Display the content (you may need to modify this based on the actual content type)
    except Exception as e:
        st.error(f"An error occurred: {e}")

#Create the tabs
tab1, tab2 = st.tabs(["Interactive Log Viewer", "City information"])


#Creates sidebar of buttons
st.sidebar.header("Video Logs")   
try:
    bucket_contents = s3.list_objects(Bucket=BUCKET_NAME)['Contents']
    
    for obj in bucket_contents:
        button_clicked = st.sidebar.button(obj['Key'])
        #if specific video is pressed
        if button_clicked:
            # Retrieve the content of the object from S3
            response = s3.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
            with tab1:
                display_video(obj['Key'])

except Exception as e:
    st.error(f"An error occurred: {e}")


   
#Map Viewer Tab
with tab2:
    st.header("All of the maps with buttons go here")

    # Create a horizontal layout for buttons
    col1, col2, col3, col4 = st.columns(4)

    # Place buttons in the columns
    button1 = col1.button("Show Information 1")
    button2 = col2.button("Show Information 2")
    button3 = col3.button("Show Information 3")
    button4 = col4.button("Show Information 4")

    with st.container(height=500, border=True) as container:
        if button1:
            #st.image("images/dog.jpg")
            st.plotly_chart(graph1)
        if button2:
            st.image("images/cat.jpg", use_column_width=True, )
        if button3:
            st.image("images/bird.jpg")
        if button4:
            st.write("I'm too lazy to find another image!")
