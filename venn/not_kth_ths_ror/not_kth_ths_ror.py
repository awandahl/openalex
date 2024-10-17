import requests
from collections import Counter
import csv
import time
import re
import os
from datetime import datetime
import pandas as pd

# Configuration settings
START_YEAR = 2023
END_YEAR = 2024
EMAIL = "aw@kth.se"
API_KEY = None  # Add your API key if you have one

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

def get_raw_affiliations(start_year, end_year, email=None, api_key=None):
    base_url = "https://api.openalex.org/works"
    headers = {}
    if email:
        headers['User-Agent'] = f'mailto:{email}'
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    all_affiliations = []
    processed_years = set()
    latest_csv = get_latest_csv_file('potential_kth_affiliations_')
    if latest_csv:
        processed_years = get_processed_years(latest_csv)
    print(f"Already processed years: {processed_years}")

    kth_ror = "https://ror.org/026vcq606"
    ths_ror = "https://ror.org/0519hrc61"

    search_terms = (
        '("KTH" OR '
        '(("roy inst" OR '
        '"royal in-stitute" OR '
        '"royal inititute" OR '
        '"royal institut" OR '
        '"royal institute" OR '
        '"royal institite" OR '
        '"royal institution" OR '
        '"royal institue" OR '
        '"royal insititu" OR '
        '"royal insitute" OR '
        '"royal inst" OR '
        '"royal inst." OR '
        '"royal intitute" OR '
        '"royal istitute" OR '
        '"royal lnstitute" OR '
        '"royal lnstitufe" OR '
        '"royal lnstltute") AND'
        '"tech") OR '
        '(("kgl" OR '
        '"kgl." OR '
        '"kungl" OR '
        '"kungl." OR '
        '"kungliga") AND '
        '"tekn") OR '
        '"r inst of technol" OR '
        '"r inst. of technol." OR '
        '"r. inst. of tech." OR '
        '"r. inst. of technol" OR '
        '"r. inst. of technol." OR '
        '"royal tech" OR '
        '"institute of technology stockholm" OR '
        '"royal of technology" OR '
        '"royal school of technology" OR '
        '"royal swedish institute of technology" OR '
        '"royal university of technology" OR '
        '"royal college of technology" OR '
        '"royalinstitute" OR '
        '"alfven" OR '
        '"alfvén" OR '
        '"10044 stockholm" OR '
        '"100 44 stockholm") NOT '
        '"khyber"'
    )

    for year in range(start_year, end_year + 1):
        if year in processed_years:
            print(f"Skipping year {year} as it's already processed.")
            continue

        params = {
            "filter": f"raw_affiliation_strings.search:({search_terms}),"
                      f"publication_year:{year},"
                      f"institutions.ror:!{kth_ror},"
                      f"institutions.ror:!{ths_ror}",
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
                print(f"Response content: {response.text}")
                break

            data = response.json()
            results = data.get('results', [])
            if not results:
                break

            for work in results:
                for authorship in work.get('authorships', []):
                    raw_affiliations = authorship.get('raw_affiliation_strings', [])
                    for raw_affiliation in raw_affiliations:
                        if raw_affiliation and any(term.lower() in raw_affiliation.lower() for term in search_terms.replace('"', '').split(' OR ')):
                            affiliations.append((raw_affiliation.lower(), year, work['id']))

            total_processed += len(results)
            print(f"Year {year}: Processed {total_processed} works, found {len(affiliations)} potential KTH affiliations so far.")

            if 'meta' in data and 'next_cursor' in data['meta']:
                params['cursor'] = data['meta']['next_cursor']
                page += 1
            else:
                break

            time.sleep(1)  # To avoid hitting rate limits

        all_affiliations.extend(affiliations)
        processed_years.add(year)
        print(f"Completed year {year}. Total potential affiliations: {len(all_affiliations)}")

    if all_affiliations:
        new_csv_filename = f'potential_kth_affiliations_{min(processed_years)}-{max(processed_years)}_{datetime.now().strftime("%Y%m%d")}.csv'
        df = pd.DataFrame(all_affiliations, columns=['Raw Affiliation', 'Year', 'Work ID'])
        df['Count'] = df.groupby('Raw Affiliation')['Raw Affiliation'].transform('count')
        df = df.sort_values('Count', ascending=False).drop_duplicates(subset=['Raw Affiliation'])
        df.to_csv(new_csv_filename, index=False)
        print(f"Saved potential KTH affiliations to {new_csv_filename}")
        return df['Raw Affiliation'].tolist(), df['Year'].tolist(), df['Count'].tolist(), df['Work ID'].tolist()
    else:
        print("No new potential affiliations found.")
        return [], [], [], []


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
if __name__ == "__main__":
    print(f"Email being used: {EMAIL}")
    affiliations, years, counts, work_ids = get_raw_affiliations(START_YEAR, END_YEAR, email=EMAIL, api_key=API_KEY)

    print(f"\nTotal potential KTH affiliations found: {len(affiliations)}")
    print("\nTop 20 most common potential KTH affiliation strings:")
    for affiliation, count in Counter(affiliations).most_common(20):
        print(f"{count}: {affiliation}")

    # Read the filter strings from a text file
    with open('filter_strings.txt', 'r') as file:
        filter_strings = [line.strip().lower() for line in file.readlines()]

    # Filter out affiliations
    filtered_affiliations = [aff for aff in affiliations if not any(f in aff.lower() for f in filter_strings)]

    print(f"\nTotal affiliations: {len(affiliations)}")
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

    # Save all affiliations to a CSV file
    df = pd.DataFrame({'Raw Affiliation': affiliations, 'Year': years, 'Count': counts, 'Work ID': work_ids})
    df.to_csv(f'all_potential_kth_affiliations_{START_YEAR}-{END_YEAR}_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
    print(f"\nSaved all potential KTH affiliations to CSV file.")

