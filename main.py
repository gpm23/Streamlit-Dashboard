import streamlit as st
import numpy as np
import plotly.express as px


st.write("my name is Gabriel")


fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
fig.show()

st.plotly_chart(fig)