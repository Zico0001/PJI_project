import streamlit as st
import pandas as pd
import folium
import base64
import os
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from Data_Preproccess import add_geocoded_columns_to_excel
# Function to generate the map based on the selected year and workshop
# Function to generate the map based on the selected year
def generate_map(data):


    # Create a map centered at an approximate location
    m = folium.Map(location=[28, -82], zoom_start=5, tiles='cartodb dark_matter')

    # Add total people served and total projects as a title
    total_people_attended = 19150  # Replace with your actual data
    total_workshops = 1200  # Replace with your actual data
    # Add a custom HTML overlay at the top (modified)
    html = f"""
    <div style="
      position: fixed;
      top: 10px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 9999;
      background-color: rgba(205, 127, 50, 0.7);
      color: white;
      opacity: 0.5;
      padding: 10px 20px;
      border-radius: 10px;
      font-size: 2vw; /* Use viewport width for font size */
      font-family: Arial, sans-serif;
      max-width: 90%; /* Limit width to 90% of viewport */
  ">
      <b>Total People Attended:</b> {total_people_attended:,} | <b>Total Workshops:</b> {total_workshops:,}
  </div>
  """
    m.get_root().html.add_child(folium.Element(html))

    # Create a MarkerCluster
    marker_cluster = MarkerCluster().add_to(m)

    # Define data with actual image URLs from Wikimedia Commons
    # Add markers for the filtered data
    circle_scaling_factor = 0.001

    for entry in data:
        # Calculate radius and font size based on people served
        radius = int(entry["People Attended"]) * circle_scaling_factor

        # Tooltip content for hover
        tooltip_content = f"""
        <div style="width:150px">
            <p>{entry['People Attended']} people Attended</p>
            <img src="{entry['Img']}" width="150px">
        </div>
        """

        # Add the circle marker to the marker cluster
        marker = folium.CircleMarker(
            location=[entry["lat"], entry["lon"]],
            radius=radius,
            color="yellow",
            fill=True,
            fill_color="yellow",
            fill_opacity=0.7,
            tooltip=folium.Tooltip(tooltip_content),
        )

        marker.add_to(marker_cluster)

    # Display the map

    return m

# Streamlit app
def main():
    st.title("PJI Principles Map Viewer")

    # Upload dataset
    uploaded_file = st.file_uploader("Upload your dataset (CSV format):", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        address_column="Address"
        people_column="People Attended"
        img_column="Img"
        api_key="******************"
        df = add_geocoded_columns_to_excel(uploaded_file, address_column, people_column, img_column, api_key)

        data = df.to_dict(orient="records")

       

        # Generate and display the map
        map_object = generate_map(data)
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
