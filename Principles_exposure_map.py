import streamlit as st
import pandas as pd
import folium
import base64
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
        
    # Add total people served and total projects as a title
    total_people_attended = 19150  # Replace with your actual data
    total_workshops = 1200  # Replace with your actual data

    # Add JavaScript for interactivity
    m.get_root().html.add_child(folium.Element("""
    <style>
        #map-container {
            position: relative;
            width: 100%;
            height: 100vh;
        }
        #controls {
            position: absolute;
            top: 5px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background: rgba(0,0,0,0.7);
            padding: 10px;
            border-radius: 5px;
        }
        #total-info {
            position: absolute;
            top: 40px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background: rgba(205, 127, 50, 0.7);
            color: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
    </style>
    <div id="controls">
        <select id="year-select">
            <option value="">All Years</option>
        </select>
        <select id="name-select">
            <option value="">All Workshops</option>
        </select>
    </div>
    <div id="total-info">
        number of People Exposed to PJI Principles: 0 | Total Workshops: 0
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Extract unique years and names
        const data = """ + str(data) + """;
        const yearSelect = document.getElementById('year-select');
        const nameSelect = document.getElementById('name-select');
        const totalInfo = document.getElementById('total-info');

        // Populate year dropdown
        const years = [...new Set(data.map(d => d.Year))].sort();
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            yearSelect.appendChild(option);
        });

        // Populate name dropdown
        const names = [...new Set(data.map(d => d.name))].sort();
        names.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            nameSelect.appendChild(option);
        });

        // Marker cluster group
        const markers = L.markerClusterGroup();

        // Function to filter and display markers
        function updateMarkers() {
            // Clear existing markers
            markers.clearLayers();

            // Filter data
            const selectedYear = yearSelect.value;
            const selectedName = nameSelect.value;

            const filteredData = data.filter(entry =>
                (selectedYear === '' || entry.Year == selectedYear) &&
                (selectedName === '' || entry.name === selectedName)
            );

            // Update total info
            const totalPeopleserved = filteredData.reduce((sum, entry) => sum + entry.people_served, 0);
            const totalWorkshops = filteredData.length;
            totalInfo.innerHTML = `Number of People Exposed to PJI Principles: ${totalPeopleserved.toLocaleString()} | Total Workshops: ${totalWorkshops}`;

            // Add markers
            filteredData.forEach(entry => {
                const radius = Math.max(5, entry.people_served * 0.001);
                const marker = L.circleMarker([entry.lat, entry.lon], {
                    radius: radius,
                    color: 'yellow',
                    fillColor: 'yellow',
                    fillOpacity: 0.7
                });

                // Add tooltip
                marker.bindTooltip(`
                    <div style="width:200px;">
                        <h4>${entry.name} Workshop</h4>
                        <p>${entry.people_served} people served</p>
                        <img src="${entry.image_url}" width="180px">
                    </div>
                `);

                markers.addLayer(marker);
            });
        }

        // Add event listeners
        yearSelect.addEventListener('change', updateMarkers);
        nameSelect.addEventListener('change', updateMarkers);

        // Initial marker update
        updateMarkers();
    });
    </script>
    """))    
    
    
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
    st.title("PJI Principles Map Viewer")

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
