#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 15:37:35 2025

@author: francescaareselucini
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io


# Title of the app
st.title("Bloomberg Scoring")

# Instructions
st.markdown("""
### Instructions:
1. Upload your input company data Excel file (with an 'Employee History' column).
2. Adjust the weights of scoring parameters as needed.
3. Click "Process Data" to calculate scores and view results.
4. Download the updated Excel file with scores and see the community metrics (median & average).
""")

# Function to load Top VCs from a file
def load_top_vcs(file_path="VCtop_latest.txt"):
    try:
        with open(file_path, 'r') as file:
            return {line.strip() for line in file}
    except FileNotFoundError:
        st.error(f"Could not find the Top VCs file at {file_path}. Please ensure the file is available.")
        st.stop()

# Load Top VCs
TOP_VCS = load_top_vcs()

growth_year = datetime.now().year

# File Uploads
uploaded_file = st.file_uploader("Upload Company Data Excel File", type=["xlsx"])
# top_vcs_file = st.file_uploader("Upload Top VCs Text File", type=["txt"])

# Sidebar for weight adjustments
st.sidebar.header("Adjust Weights")
weights = {
    'VC Score': st.sidebar.slider("VC Score Weight", 0.0, 1.0, 0.30, 0.01),
    'Funding Valuation Score': st.sidebar.slider("Funding Valuation Score Weight", 0.0, 1.0, 0.30, 0.01),
    # 'Raised Score': st.sidebar.slider("Raised Score Weight", 0.0, 1.0, 0.14, 0.01),
    # 'Recent Financing Score': st.sidebar.slider("Recent Financing Score Weight", 0.0, 1.0, 0.1, 0.01),
    'Company Growth Score': st.sidebar.slider("Company Growth Score Weight", 0.0, 1.0, 0.25, 0.01),
    'Emerging and Verticals Score': st.sidebar.slider("Emerging and Verticals Score Weight", 0.0, 1.0, 0.15, 0.01),
   #'Innovation ChatGPT Score': st.sidebar.slider("Innovation ChatGPT Score Weight", 0.0, 1.0, 0.15, 0.01),
    #'Media Outreach ChatGPT Score': st.sidebar.slider("Media Outreach ChatGPT Score Weight", 0.0, 1.0, 0.15, 0.01),
  #'Judges Score': st.sidebar.slider("Judges Score Weight", 0.0, 1.0, 0.05, 0.01),
}


# Helper function to parse employee history
def parse_employee_data(row):
    if isinstance(row, str):
        entries = row.split(', ')
        return {int(entry.split(': ')[0]): int(entry.split(': ')[1]) for entry in entries}
    return {}


# Function to calculate growth between two years
def calculate_growth(data, start_year, end_year):
    if start_year in data and end_year in data:
        return ((data[end_year] - data[start_year]) / data[start_year]) * 100
    return None


# Function to add 'growth to 2024' column based on the last 5 years or the latest available consecutive years
def add_growth_column(df, starting_year):
    def calculate_growth(parsed_data, start_year):
        # Get all available years in the data
        years = sorted(parsed_data.keys(), reverse=True)  # Sort descending
        # Find the latest consecutive years within the range
        recent_years = [year for year in years if year <= start_year][:5]
        if len(recent_years) < 2:
            return None  # Not enough data to calculate growth
        first_year = recent_years[-1]
        last_year = recent_years[0]
        # Calculate growth between the first and last years
        return ((parsed_data[last_year] - parsed_data[first_year]) / parsed_data[first_year]) * 100

    # Parse employee history and calculate growth
    df['Parsed Data'] = df['Employee History'].apply(parse_employee_data)
    df['growth to 2025'] = df['Parsed Data'].apply(lambda x: calculate_growth(x, starting_year))
    return df



# Scoring function for Top VCs 0 takes into account spaces etc...

def score_vc(company):
    active_investors = company['Active Investors'].split(',') if pd.notna(company['Active Investors']) else []
    past_investors = company['Former Investors'].split(',') if pd.notna(company['Former Investors']) else []
    all_investors = {inv.strip().lower() for inv in active_investors + past_investors}

    top_vcs_normalized = {vc.strip().lower() for vc in TOP_VCS}
    matches = all_investors.intersection(top_vcs_normalized)

    return 10 if len(matches) > 1 else 7 if len(matches) == 1 else 0


def score_funding_valuation(company):
    valuation = company['Last Known Valuation']
    if valuation >= 5000:
        return 10
    elif valuation >= 2000:
        return 8
    elif valuation >= 1000:
        return 7
    elif valuation > 750:
        return 6
    elif valuation > 500:
        return 5
    elif valuation > 250:
        return 4
    elif valuation > 100:
        return 3
    elif valuation >= 50:
        return 1
    else:
        return 0

def score_raised(company):
    raised = company['Total Raised']
    if raised >= 100:
        return 10
    elif raised > 90:
        return 9
    elif raised > 80:
        return 8
    elif raised > 70:
        return 7
    elif raised > 70:
        return 6
    elif raised > 50:
        return 5
    elif raised > 40:
        return 4
    elif raised > 30:
        return 3
    elif raised > 20:
        return 2
    elif raised > 10:
        return 1
    else:
        return 0



# def recent_financing(company, reference_date_str):
#     # Parse the reference date
#     reference_date = datetime.strptime(reference_date_str, '%Y-%m-%d')
#     # Check if 'Last Financing Date' is within the last 12 months
#     last_financing_date = pd.to_datetime(company['Last Financing Date'], errors='coerce')
#     recent_raise = 0
#     large_financing = 0

#     if pd.notna(last_financing_date) and last_financing_date > reference_date - timedelta(days=365):
#         # 1 point for raising in the last 12 months
#         recent_raise = 5

#         # Check if 'Last Financing Size' > 500
#         last_financing_size = company.get('Last Financing Size', 0)
#         if pd.notna(last_financing_size) and last_financing_size > 500:
#             large_financing = 5

#     # Combine points
#     return recent_raise + large_financing





def evaluate_company_growth(row):
    current_year = datetime.now().year
    years_in_operation = current_year - row['Year Founded']
    growth = row.get(f'growth to {growth_year}', None)
    if years_in_operation >= 4:
        # Companies 4 years or older
        if growth >= 1000:
            return 10
        elif growth > 900:
            return 9
        elif growth > 800:
            return 8
        elif growth > 700:
            return 7
        elif growth > 600:
            return 6
        elif growth > 500:
            return 5
        elif growth > 400:
            return 4
        elif growth > 300:
            return 3
        elif growth > 0:
            return 1
        else:
            return 0
    else:
        # Companies younger than 4 years
        if growth > 400:
            return 10
        elif growth > 200:
            return 6
        elif growth > 100:
            return 3
        else:
            return 0

# %%%

def score_emerging_and_verticals(company):
    # Check if 'Emerging Spaces' is not empty
    emerging_space_score = pd.notna(company['Emerging Spaces']) and bool(company['Emerging Spaces'].strip())

    # Check if 'Verticals' includes any of the target keywords
    verticals_score = False
    if pd.notna(company['Verticals']):
        # Normalize the verticals column to lowercase and strip extra spaces
        verticals = [v.strip().lower() for v in company['Verticals'].split(',')]
        # Define target keywords, normalized to lowercase
        target_keywords = {
            'artificial intelligence & machine learning',
            'robotics & drones',
            'cybersecurity',
            'space technology',
            'life sciences',
            'nanotechnology',
            'quantum computing'
            'autonomous cars'
        }
        # Check if any target keyword is present in the verticals
        verticals_score = any(keyword in verticals for keyword in target_keywords)

    # Assign 1 point if either condition is met
    return 10 if emerging_space_score or verticals_score else 0


# def calculate_overall_score(row, weights):
#     total_score = sum(row[key] * weights[key] for key in weights)
#     return total_score

# def calculate_overall_score(row, weights):
#     total_score = 0
#     for key in weights:
#         if key in row:
#             total_score += row[key] * weights[key]
#         else:
#             st.warning(f"Missing score column: '{key}' — skipping it in calculation.")
#     return total_score

# deals with missing values and calculates weighted average
def calculate_overall_score(row, weights):
    total_score = 0
    total_weight = 0
    for key in weights:
        if key in row and pd.notna(row[key]):
            total_score += row[key] * weights[key]
            total_weight += weights[key]
        else:
            st.warning(f"Missing score column: '{key}' — skipping it in calculation.")
    return total_score / total_weight if total_weight > 0 else 0

# Integration in Streamlit processing pipeline
# Process data
if st.button("Process Data"):
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
         
        # Add growth column
        if 'Employee History' in df.columns:
            df = add_growth_column(df, growth_year)
        else:
            st.error("The input file must contain an 'Employee History' column.")
            st.stop()
        
        # Fill other missing values
        df['Total Raised'] = df['Total Raised'].fillna(df['Last Known Valuation'] / 4)
        # df = df.dropna(subset=["Last Known Valuation"])
        df['Last Known Valuation'] = df['Last Known Valuation'].fillna(df['Total Raised']*4)
        
        # Apply scoring functions
        df['VC Score'] = df.apply(score_vc, axis=1)
        df['Funding Valuation Score'] = df.apply(score_funding_valuation, axis=1)
        df['Raised Score'] = df.apply(score_raised, axis=1)
        # df['Recent Financing Score'] = df.apply(lambda x: recent_financing(x, '2024-11-18'), axis=1)
        # df['HQ Location Score'] = df.apply(check_hq_location, axis=1)
        df['Company Growth Score'] = df.apply(evaluate_company_growth, axis=1)
        df['Emerging and Verticals Score'] = df.apply(score_emerging_and_verticals, axis=1)
        df['Overall Score'] = df.apply(lambda x: calculate_overall_score(x, weights), axis=1)
        
        # Sort the DataFrame by 'Overall Score' in descending order
        df = df.sort_values(by='Overall Score', ascending=False)
        
        # Calculate metrics
        median_score = df['Overall Score'].median()
        average_score = df['Overall Score'].mean()
        
        # Display metrics
        st.write(f"Median Overall Score: {median_score:.2f}")
        st.write(f"Average Overall Score: {average_score:.2f}")
        
        # Create an in-memory Excel file for download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)  # Reset the buffer
        
        # Provide download option
        st.download_button(
            label="Download Updated Data",
            data=output,
            file_name="bloomberg_scoring.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Please upload both the company data file and the Top VCs file.")
