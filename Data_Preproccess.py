import os
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

# Initialize the geocoder
geolocator = Nominatim(user_agent="geoapiExercises")

# Function to geocode an address
def geocode_address(address):
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        # Retry once if there's a timeout
        time.sleep(1)
        return geocode_address(address)
    except Exception as e:
        print(f"Error geocoding {address}: {e}")
        return None, None

def process_excel_all_sheets_for_geocoding(excel_file, address_column, people_column, img_column):
    """
    Processes all sheets in an Excel file, extracts required columns, geocodes addresses,
    and saves a consolidated CSV file.

    Parameters:
        excel_file (str): Path to the input Excel file.
        address_column (str): Name of the column containing addresses.
        people_column (str): Name of the column containing people attended data.
        img_column (str): Name of the column containing image data.

    Returns:
        str: Path to the saved consolidated CSV file.
    """
    # Read all sheets into a dictionary of DataFrames
    sheets = pd.read_excel(excel_file, sheet_name=None)

    # Create an empty list to store results from all sheets
    all_results = []

    for sheet_name, data in sheets.items():
        print(f"Processing sheet: {sheet_name}")
        
        # Ensure required columns exist in the current sheet
        for col in [address_column, people_column, img_column]:
            if col not in data.columns:
                print(f"Skipping sheet '{sheet_name}' - Missing column '{col}'.")
                continue

        # Extract required columns and drop rows with NaN values
        relevant_data = data[[address_column, people_column, img_column]].dropna()

        # Create a list to store geocoded results for the current sheet
        sheet_results = []

        # Geocode each address
        for _, row in relevant_data.iterrows():
            address = row[address_column]
            people_attended = row[people_column]
            img = row[img_column]

            # Geocode the address
            lat, lon = geocode_address(address)

            # Append the results
            sheet_results.append({
                "Sheet Name": sheet_name,
                "Latitude": lat,
                "Longitude": lon,
                "People Attended": people_attended,
                "Img": img
            })

        # Append results from the current sheet to the main list
        all_results.extend(sheet_results)

    # Convert all results to a single DataFrame
    consolidated_results_df = pd.DataFrame(all_results)

    # Automatically generate output CSV name based on the input Excel file name
    base_name = os.path.splitext(os.path.basename(excel_file))[0]
    output_csv = f"{base_name}_geocoded_all_sheets.csv"

    # Save to CSV
    consolidated_results_df.to_csv(output_csv, index=False)
    print(f"Processed data from all sheets saved to '{output_csv}'")

    return output_csv

# Example Usage
excel_file = "example.xlsx"  # Path to your Excel file
address_column = "Address"  # Column containing addresses
people_column = "People Attended"  # Column containing people attended data
img_column = "Img"  # Column containing image data

try:
    output_csv_path = process_excel_all_sheets_for_geocoding(
        excel_file, address_column, people_column, img_column
    )
    print(f"Output CSV file path: {output_csv_path}")
except Exception as e:
    print(f"An error occurred: {e}")
