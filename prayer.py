import pandas as pd
import pytz
from datetime import datetime
import os
import streamlit as st
from datetime import time
import random
import openpyxl

def write_data_xlsx(df,output_excel_path, sheet_name1):
    #Write the DataFrame to the Excel file with sheet name "tab100"
    #with pd.ExcelWriter(output_excel_path, engine='openpyxl',  mode='a') as writer:
    #df.to_excel(writer, sheet_name = sheet_name1, index=False, if_sheet_exists='append')
    #Check if the file exists
    file_exists = is_file_exist(output_excel_path)
    #check if the Excel file is open
    check_open = is_file_open(output_excel_path)
    #check if sheet exist
    sheet_exist = is_sheet_exist(output_excel_path, sheet_name1)

    if file_exists:
        if check_open:
            with pd.ExcelWriter(output_excel_path, mode='a') as excel_writer:
                if sheet_exist:
                    excel_writer.book.remove(excel_writer.sheets[sheet_name1])
                df.to_excel(excel_writer, sheet_name=sheet_name1, index=False)
    else:
        with pd.ExcelWriter(output_excel_path) as excel_writer:
            df.to_excel(excel_writer, sheet_name=sheet_name1, index=False)

def is_file_exist(file_path):
    file_exists = os.path.isfile(file_path)
    return file_exists

def is_file_open(file_path):
    if is_file_exist(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore'):
                return True #the file is not open, it is ready to read and write
        except IOError:
            return False
    else:
        return False
    
def is_sheet_exist(file_path, sheet_name):
    if is_file_open(file_path):
        try:
            with pd.ExcelFile(file_path) as xls:
                return sheet_name in xls.sheet_names
        except FileNotFoundError:
            return False        
    else:
        return False

def load_table(table, sheet, initial):

    df = pd.read_excel(table, sheet_name = sheet)

    #make a diff between timezone table and other tables
    if initial:
        # Convert 'Date' column to datetime format
        df['Date'] = pd.to_datetime(df['Date'])

        # Convert prayer times to datetime time objects
        for column in ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
            #df[column] = pd.to_datetime(df[column], format='%H:%M:%S').dt.time
            df[column] = pd.to_datetime(df[column], format='%I:%M %p').dt.strftime('%H:%M:%S')
    else:
        df['Time_Zone'] = df['Continent'] + '/' + df['City']

    return df

def check_prayer_overlap(df, date, start_time, end_time):
    
    lesson_date = datetime.strptime(date, '%Y-%m-%d')  # Set this to the lesson date
    lesson_start = datetime.strptime(start_time, '%H:%M:%S').time()
    lesson_end = datetime.strptime(end_time, '%H:%M:%S').time()

    # Filter the dataframe for the given date
    day_prayers = df[df['Date'] == lesson_date]
    prayers_in_range = []

    # Check if any prayer time falls within the lesson time range
    if not day_prayers.empty:
        day_prayers = day_prayers.iloc[0]  # Get the single row for the date
        for prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
            prayer_datetime = day_prayers[prayer]
            prayer_datetime_agg = datetime.strptime(prayer_datetime, '%H:%M:%S').time()
            if lesson_start <= prayer_datetime_agg <= lesson_end:
                lesson_start1 = datetime.combine(lesson_date, lesson_start)
                prayer_datetime_agg1 = datetime.combine(lesson_date, prayer_datetime_agg)
                time_diff = prayer_datetime_agg1 - lesson_start1
                conac = f" {prayer}: {prayer_datetime_agg} ({time_diff})"
                prayers_in_range.append(conac)
    
    if prayers_in_range:
        return f"{', '.join(prayers_in_range)}."
    else:
        return None

def convert_times(start_date_str, start_time_str, end_date_str, end_time_str, source_tz_str, target_city):
    # Helper function to convert a single datetime
    start_date_converted, start_time_converted = convert_time(start_date_str, start_time_str, source_tz_str, target_city)
    _, end_time_converted = convert_time(end_date_str, end_time_str, source_tz_str, target_city)
    
    return start_date_converted, start_time_converted, end_time_converted

def convert_time(date_str, time_str, source_tz_str, target_city):

    # Combine the date and time strings into one datetime object
    source_time_str = f"{date_str} {time_str}"
    source_tz = pytz.timezone(source_tz_str)
    
    # Parse the combined date and time string
    source_time = datetime.strptime(source_time_str, '%Y-%m-%d %H:%M:%S')
    
    # Localize the datetime to the source timezone
    source_time = source_tz.localize(source_time)
    
    # Define the timezone for the target city
    target_tz = pytz.timezone(target_city)
    
    # Convert the time to the target city's timezone
    target_time = source_time.astimezone(target_tz)
    
    # Split the result into separate date and time strings
    target_date_str = target_time.strftime('%Y-%m-%d')
    target_time_str = target_time.strftime('%H:%M:%S')
    
    return target_date_str, target_time_str


if __name__ == "__main__":

    # Streamlit app interface
    st.title("Prayer Time: IDSchool")
    # Display the logo
    st.image("logo.png", width=200)  # You can adjust the width to fit the size

    # Load the CSV file
    source_tz_str = 'Africa/Algiers'
    sheet_name = 'Timezone'
    table = 'prayer.xlsx'
    zones_df = load_table(table, sheet_name, False)
    # Initialize an empty string
    result = ""

    # Example Usage
    #lesson_date = '2024-09-22'
    #start_time = '16:30:00'
    #end_time = '18:00:00'
    # Define a default time
    default_stime = time(15, 0)
    default_etime = time(16, 30)

    # User input for numbers
    lesson_date = st.date_input("Enter a date", datetime.now())
    start_time = st.time_input("Enter start time", value=default_stime)
    end_time = st.time_input("Enter end time", value=default_etime)
    
    # Perform calculation when the button is clicked
    if st.button("Find"):
        
        results = []  # Initialize a list to store results

        for index, row in zones_df.iterrows():
            target_zone = row['Time_Zone']
            target_city = row['City']
            cities_df = load_table(table, target_city, True)
            converted_ldate, converted_stime, converted_etime = convert_times(lesson_date, start_time, lesson_date, end_time, source_tz_str, target_zone)
            result = check_prayer_overlap(cities_df, converted_ldate, converted_stime, converted_etime)
            result_str = f"{target_city}: {result}" if result is not None else f"{target_city}: /"
            
            # Generate a color for each city name (you can use a list of colors or a function to vary colors)
            color = "#"+''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
            
            result_str = f"<b><font color='{color}'>{target_city}</font></b>: {result if result is not None else ' /'}"
            
            results.append(result_str)  # Add result to the list

        # Print each result on a new line
        for result in results:
            #st.write(result)
            st.markdown(result, unsafe_allow_html=True)