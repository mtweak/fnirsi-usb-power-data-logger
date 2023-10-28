import streamlit as st
import pandas as pd
import time
import subprocess
from io import StringIO
import time
import plotly.express as px

#Make wide
st.set_page_config(layout="wide")
st.title('Real-time Graphs from live.txt')


# User input for how many lines to fetch from the end of the file
col1, col2 = st.columns(2)
with col1:
    num_lines = st.slider("Number of lines to fetch from the end:", min_value=10, max_value=5000, value=1000, step=100)

with col2: 
    update_interval = float(st.text_input("Enter update interval in seconds:", value="0.5"))

try:
    num_lines = int(num_lines)
except ValueError:
    st.warning("Please enter a valid integer.")
    num_lines = 1000

# Define a function to load data
#@st.cache_data(ttl=5)
def load_data(n):
    cmd = ['tail', '-n', str(n), '/tmp/live.txt']
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Read the fetched data using predefined headers
    headers = ["timestamp", "sample_in_packet", "voltage_V", "current_A", "dp_V", "dn_V", "temp_C_ema", "energy_Ws", "capacity_As"]
    data = pd.read_csv(StringIO(result.stdout), delim_whitespace=True, names=headers, header=None)

    return data

data = load_data(num_lines)

# Create chart subheaders
st.subheader("Computed Power (W)")
power_chart = st.empty()

#Set min and max values for y axis in a text box
_, col1, col2 = st.columns([5, 1, 1])
with col1:
    ymin = st.text_input("ymin:", value="")
    ymin_value = st.empty()

with col2:
    ymax = st.text_input("ymax:", value="")
    ymax_value = st.empty()
    yavg_value = st.empty()
    

st.subheader("Current (A)")
current_chart = st.empty()

st.subheader("Voltage (V)")
voltage_chart = st.empty()


other_headers = {col: st.subheader(col) for col in ['dp_V', 'dn_V', 'temp_C_ema', 'energy_Ws', 'capacity_As']}
other_charts = {col: st.empty() for col in ['dp_V', 'dn_V', 'temp_C_ema', 'energy_Ws', 'capacity_As']}


while True:
    data = load_data(num_lines)
    
    # Compute power
    data['power_W'] = data['voltage_V'] * data['current_A']
    
    ymin_value.text(f"{data['power_W'].min()}")
    ymax_value.text(f"{data['power_W'].max()}")
    yavg_value.text(f"avg: {data['power_W'].mean():.2f}")

    # Update charts
    if ymin == "":
        ymin = data['power_W'].min()
    else:
        ymin = float(ymin)
    
    if ymax == "":
        #Set to the max value in the data
        ymax = data['power_W'].max()
    else:
        ymax = float(ymax)


    fig = px.line(data, x='timestamp', y='power_W', title='Power (W)', range_y=[ymin, ymax])
    fig.update_traces(line=dict(width=1))
    power_chart.plotly_chart(fig, use_container_width=True)
    current_chart.plotly_chart(px.line(data, x='timestamp', y='current_A', title='Current (A)'), use_container_width=True)
    voltage_chart.plotly_chart(px.line(data, x='timestamp', y='voltage_V', title='Voltage (V)'), use_container_width=True)

    # Update other columns
    #for col in ['dp_V', 'dn_V', 'temp_C_ema', 'energy_Ws', 'capacity_As']:
    #    other_charts[col].line_chart(data[col])

    # Sleep for a short duration before re-reading the file
    time.sleep(update_interval)
