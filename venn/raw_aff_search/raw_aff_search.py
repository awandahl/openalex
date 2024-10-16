import requests
from collections import Counter
import csv
import time
import re
import os
from datetime import datetime
import pandas as pd

# Configuration settings
USE_API = False
ROR_ID = "https://ror.org/026vcq606"
START_YEAR = 1990
END_YEAR = 2025
EMAIL = "aw@kth.se"
API_KEY = None

def get_latest_csv_file(prefix):
    csv_files = [f for f in os.listdir('.') if f.startswith(prefix) and f.endswith('.csv')]
    return max(csv_files) if csv_files else None

def get_processed_years(filename):
    if not filename or not os.path.exists(filename):
        return set()
    try:
        df = pd.read_csv(filename)
        return set(df['Year'].unique())
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return set()

def get_raw_affiliations(ror_id, start_year, end_year, email=None, api_key=None):
    base_url = "https://api.openalex.org/works"
    headers = {}
    if email:
        headers['User-Agent'] = f'mailto:{email}'
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    all_affiliations = []
    processed_years = set()

    latest_csv = get_latest_csv_file('raw_affiliations_')
    if latest_csv:
        processed_years = get_processed_years(latest_csv)
        print(f"Already processed years: {processed_years}")

    for year in range(start_year, end_year + 1):
        if year in processed_years:
            print(f"Skipping year {year} as it's already processed.")
            continue

        params = {
            "filter": f"institutions.ror:{ror_id},publication_year:{year}",
            "select": "authorships",
            "per-page": 200,
            "cursor": "*"
        }
        affiliations = []
        total_processed = 0
        page = 1

        while True:
            print(f"Fetching page {page} for year {year}")
            response = requests.get(base_url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"Error: API request failed with status code {response.status_code}")
                break

            data = response.json()
            results = data.get('results', [])
            if not results:
                break

            for work in results:
                for authorship in work.get('authorships', []):
                    for affiliation in authorship.get('affiliations', []):
                        if "https://openalex.org/I86987016" in affiliation.get('institution_ids', []):
                            raw_affiliation = affiliation.get('raw_affiliation_string')
                            if raw_affiliation:
                                affiliations.append((raw_affiliation.lower(), year))

            total_processed += len(results)
            print(f"Year {year}: Processed {total_processed} works, found {len(affiliations)} KTH affiliations so far.")

            if 'meta' in data and 'next_cursor' in data['meta']:
                params['cursor'] = data['meta']['next_cursor']
                page += 1
            else:
                break

            time.sleep(1)  # To avoid hitting rate limits

        all_affiliations.extend(affiliations)
        processed_years.add(year)
        print(f"Completed year {year}. Total affiliations: {len(all_affiliations)}")
    
    if all_affiliations:
        # Save results to CSV
        new_csv_filename = f'raw_affiliations_{min(processed_years)}-{max(processed_years)}_{datetime.now().strftime("%Y%m%d")}.csv'
        df = pd.DataFrame(all_affiliations, columns=['Raw Affiliation', 'Year'])
        
        # Deduplicate and count
        df['Count'] = df.groupby('Raw Affiliation')['Raw Affiliation'].transform('count')
        df = df.sort_values('Count', ascending=False).drop_duplicates(subset=['Raw Affiliation'])
        
        df.to_csv(new_csv_filename, index=False)
        print(f"Saved sorted and deduplicated affiliations to {new_csv_filename}")
        return df['Raw Affiliation'].tolist(), df['Year'].tolist(), df['Count'].tolist()
    else:
        print("No new affiliations found.")
        return [], [], []

def load_affiliations_from_csv():
    latest_csv = get_latest_csv_file('raw_affiliations_')
    if not latest_csv:
        print("No CSV file found.")
        return [], [], []
    
    df = pd.read_csv(latest_csv)
    print(f"Loaded affiliations from {latest_csv}")
    
    # Convert to lowercase for case insensitivity
    df['Raw Affiliation'] = df['Raw Affiliation'].str.lower()
    
    # Deduplicate and count
    deduplicated_df = df.groupby('Raw Affiliation').agg({
        'Year': 'first',  # Keep the first year for each unique affiliation
        'Raw Affiliation': 'count'  # Count occurrences
    }).rename(columns={'Raw Affiliation': 'Count'}).reset_index()
    
    # Sort by count in descending order
    deduplicated_df = deduplicated_df.sort_values('Count', ascending=False)
    
    # Save the updated, deduplicated, and sorted CSV
    updated_csv = f'raw_affiliations_deduplicated_{pd.Timestamp.now().strftime("%Y%m%d")}.csv'
    deduplicated_df.to_csv(updated_csv, index=False)
    print(f"Updated, deduplicated, and sorted affiliations saved to {updated_csv}")
    
    return deduplicated_df['Raw Affiliation'].tolist(), deduplicated_df['Year'].tolist(), deduplicated_df['Count'].tolist()

def save_filtered_affiliations(filtered_affiliation_counts):
    latest_csv = get_latest_csv_file('filtered_affiliations_')
    if latest_csv:
        existing_df = pd.read_csv(latest_csv)
        new_df = pd.DataFrame(list(filtered_affiliation_counts.items()), columns=['Filtered Affiliation String', 'Count'])
        combined_df = pd.concat([existing_df, new_df])
    else:
        combined_df = pd.DataFrame(list(filtered_affiliation_counts.items()), columns=['Filtered Affiliation String', 'Count'])
    
    combined_df['Filtered Affiliation String'] = combined_df['Filtered Affiliation String'].str.lower()
    combined_df = combined_df.groupby('Filtered Affiliation String')['Count'].sum().reset_index()
    combined_df = combined_df.sort_values('Count', ascending=False)
    new_csv_filename = f'filtered_affiliations_{datetime.now().strftime("%Y%m%d")}.csv'
    combined_df.to_csv(new_csv_filename, index=False)
    print(f"Saved filtered affiliations to {new_csv_filename}")

# Main script
if USE_API:
    print(f"Email being used: {EMAIL}")
    affiliations, years, counts = get_raw_affiliations(ROR_ID, START_YEAR, END_YEAR, email=EMAIL, api_key=API_KEY)
else:
    print("Loading affiliations from saved CSV...")
    affiliations, years, counts = load_affiliations_from_csv()

# Filter out affiliations containing "KTH" or "Royal Institute of Technology"
# filtered_affiliations = [aff for aff in affiliations if 'kth' not in aff.lower() and 'royal institute of technology' not in aff.lower()]

# Read the filter strings from a text file
with open('filter_strings.txt', 'r') as file:
    filter_strings = [line.strip().lower() for line in file.readlines()]

# Filter out affiliations
filtered_affiliations = [aff for aff in affiliations if not any(f in aff.lower() for f in filter_strings)]

print(f"Total affiliations: {len(affiliations)}")
print(f"Filtered affiliations: {len(filtered_affiliations)}")

# Get the most common filtered affiliations
filtered_affiliation_counts = Counter(filtered_affiliations)
common_filtered_affiliations = filtered_affiliation_counts.most_common(100)

print("\nTop 100 most common filtered affiliation strings:")
for affiliation, count in common_filtered_affiliations:
    print(f"{count}: {affiliation}")

# Save all filtered affiliations
save_filtered_affiliations(filtered_affiliation_counts)

print("\nAll filtered affiliations have been saved.")

