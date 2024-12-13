import streamlit as st
import pandas as pd
import folium
import os
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Function to generate the map based on the selected year and workshop
def generate_map(data, year=None, names=None):
    if year == "All Years":
        f_data = data
        if names == "All Workshops":
            filtered_data = f_data
        else:
            filtered_data = [d for d in f_data if d["name"] == names]
    else:
        f_data = [d for d in data if d["Year"] == year]
        if names == "All Workshops":
            filtered_data = f_data
        else:
            filtered_data = [d for d in f_data if d["name"] == names]

    m = folium.Map(location=[28, -82], zoom_start=5, tiles='cartodb dark_matter')
    marker_cluster = MarkerCluster().add_to(m)
    circle_scaling_factor = 0.001

    for entry in filtered_data:
        radius = int(entry["people_served"]) * circle_scaling_factor
        tooltip_content = f"""
        <div style="width:150px">
            <h4>{entry['name'] + ' Workshop'}</h4>
            <p>{entry['people_served']} people served</p>
            <img src="{entry['image_url']}" width="150px">
        </div>
        """
        marker = folium.CircleMarker(
            location=[entry["lat"], entry["lon"]],
            radius=radius,
            color="orange",
            fill=True,
            fill_color="orange",
            fill_opacity=0.7,
            tooltip=folium.Tooltip(tooltip_content),
        )
        marker.add_to(marker_cluster)
    return m

# Streamlit app
def main():
    st.title("Interactive Map Viewer")

    # Upload dataset
    uploaded_file = st.file_uploader("Upload your dataset (CSV format):", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        data = df.to_dict(orient="records")

        st.sidebar.header("Filter Options")

        # Dropdowns for filtering
        years = ["All Years"] + sorted(set(d["Year"] for d in data))
        names = ["All Workshops"] + sorted(set(d["name"] for d in data))
        selected_year = st.sidebar.selectbox("Select Year", years)
        selected_workshop = st.sidebar.selectbox("Select Workshop", names)

        # Generate and display the map
        map_object = generate_map(data, year=selected_year, names=selected_workshop)
        map_html = st_folium(map_object, width=800, height=600)

        # Button to save/export map as HTML
        if st.button("Save Map as HTML"):
            map_object.save('Principles_Map.html')
            
            # Generate download link
            with open("Principles_Map.html", "rb") as f:
               html_bytes = f.read()
            encoded_html = base64.b64encode(html_bytes).decode()
            href = f'<a href="data:text/html;base64,{encoded_html}" download="Principles_Map.html">Download HTML File</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.success("Map has been saved as 'Principles_Map.html' in your working directory.")

if __name__ == "__main__":
    main()
