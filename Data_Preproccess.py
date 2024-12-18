
import pandas as pd
import openpyxl
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import requests
import time

# Function to geocode an address using LocationIQ API
def geocode_address_locationiq(address, api_key, retries=3):
    url = f"https://us1.locationiq.com/v1/search.php?key={api_key}&q={address}&format=json"
    
    for attempt in range(retries):
        try:
            response = requests.get(url)
            data = response.json()

            if len(data) > 0:
                lat = data[0]['lat']
                lon = data[0]['lon']
                return float(lat), float(lon)
            else:
                print(f"Could not geocode address: {address}")
                return None, None
        except Exception as e:
            print(f"Error geocoding {address}: {e}")
            if attempt < retries - 1:
                print("Retrying...")
                time.sleep(2)  # Adding a delay before retry
            else:
                print("Max retries reached. Could not geocode address.")
                return None, None

# Function to process each sheet, geocode addresses, and write latitude and longitude columns
def add_geocoded_columns_to_excel(excel_file, address_column, people_column, img_column, api_key):
    """
    Processes all sheets, adds Latitude and Longitude columns, and consolidates all sheets into a single file.
    
    Parameters:
        excel_file (str): Path to the input Excel file.
        address_column (str): Name of the column containing addresses.
        people_column (str): Name of the column containing the number of people served.
        img_column (str): Name of the column containing image URLs.
        api_key (str): The LocationIQ API key.
    
    Returns:
        pd.DataFrame: Consolidated DataFrame with the added Latitude and Longitude columns.
    """
    # Load workbook using openpyxl
    workbook = pd.ExcelFile(excel_file)
    sheets = workbook.sheet_names
    all_data = []

    for sheet_name in sheets:
        print(f"Processing sheet: {sheet_name}")
        data = workbook.parse(sheet_name)

        # Skip sheets without the necessary columns
        if address_column not in data.columns or people_column not in data.columns or img_column not in data.columns:
            print(f"Skipping sheet '{sheet_name}' - Missing required columns.")
            continue

        # Add Latitude and Longitude columns if they don't exist
        if "Latitude" not in data.columns:
            data["Latitude"] = None
        if "Longitude" not in data.columns:
            data["Longitude"] = None

        # Geocode each address and add latitude/longitude
        for idx, address in enumerate(data[address_column]):
            if pd.notna(address) and not data.at[idx, "Latitude"]:
                lat, lon = geocode_address_locationiq(address, api_key)
                if lat is not None and lon is not None:
                    data.at[idx, "Latitude"] = lat
                    data.at[idx, "Longitude"] = lon
                    print(f"Geocoded '{address}': Latitude = {lat}, Longitude = {lon}")

        # Append the data from this sheet to the all_data list
        all_data.append(data)

    # Consolidate all sheets into one DataFrame
    consolidated_data = pd.concat(all_data, ignore_index=True)

    # Convert the 'Img' column to hyperlinks for Excel export
    def create_hyperlink_formula(url):
        return f'=HYPERLINK("{url}", "{url}")' if pd.notna(url) else None

    consolidated_data[img_column] = consolidated_data[img_column].apply(create_hyperlink_formula)

    return consolidated_data

# Function to save the consolidated DataFrame with hyperlinks to a new Excel file
def save_dataframe_to_excel_with_hyperlinks(df, output_excel_file):
    """
    Save the DataFrame with hyperlinks to a new Excel file.
    
    Parameters:
        df (pd.DataFrame): The DataFrame to save.
        output_excel_file (str): The path where the Excel file will be saved.
    """
    wb = Workbook()
    ws = wb.active
    
    # Write the DataFrame to the Excel sheet
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)
    
    # Save the file
    wb.save(output_excel_file)
    print(f"Consolidated Excel file with hyperlinks saved to {output_excel_file}")

# Example Usage
excel_file = "test.xlsx"  # Path to your Excel file
address_column = "Address"  # Column containing addresses
people_column = "People Attended"  # Column containing people served data
img_column = "Img"  # Column containing image URLs
api_key = "API_KEY"  # Replace with your LocationIQ API key

try:
    # Get the consolidated data with Latitude and Longitude columns
    consolidated_data = add_geocoded_columns_to_excel(excel_file, address_column, people_column, img_column, api_key)
    print(consolidated_data)
    # Save the consolidated DataFrame to a new Excel file
    #output_excel = "consolidated_output_with_geocoded_data.xlsx"
    #save_dataframe_to_excel_with_hyperlinks(consolidated_data, output_excel)
except Exception as e:
    print(f"An error occurred: {e}")

