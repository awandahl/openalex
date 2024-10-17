# KTH Affiliation Extraction Script

This script is designed to extract and analyze potential KTH (Royal Institute of Technology) affiliations from the OpenAlex database. It focuses on finding affiliations that might be related to KTH but are not officially associated with KTH's ROR ID.

## Script Overview

The script is divided into several sections:

1. Imports and Configuration
2. Utility Functions
3. Main Affiliation Extraction Function
4. Filtering and Saving Functions
5. Main Execution Block

Let's break down each section:

### 1. Imports and Configuration

```python
import requests
from collections import Counter
import csv
import time
import re
import os
from datetime import datetime
import pandas as pd

# Configuration settings
START_YEAR = 2024
END_YEAR = 2024
EMAIL = "aw@kth.se"
API_KEY = None # Add your API key if you have one

This section imports necessary libraries and sets up configuration variables. You can modify START_YEAR and END_YEAR to define the range of years to search for affiliations.

2. Utility Functions


def get_latest_csv_file(prefix):
    # ...

def get_processed_years(filename):
    # ...
``

These functions help manage CSV files and track which years have already been processed.

3. Main Affiliation Extraction Function

python
def get_raw_affiliations(start_year, end_year, email=None, api_key=None):
    # ...

This is the core function of the script. It:

    Queries the OpenAlex API for works matching specific search terms related to KTH.
    Excludes works already associated with KTH's official ROR ID.
    Extracts raw affiliation strings from the results.
    Saves the extracted affiliations to a CSV file.

4. Filtering and Saving Functions

python
def save_filtered_affiliations(filtered_affiliation_counts):
    # ...

This function saves filtered affiliations to a CSV file, combining new results with existing ones if available.
5. Main Execution Block

python
if __name__ == "__main__":
    # ...

This section runs the main workflow:

    Extracts raw affiliations.
    Applies filtering based on a filter_strings.txt file.
    Displays statistics about the affiliations found.
    Saves the results to CSV files.

How to Use the Script

    Setup:
        Ensure you have Python installed with the required libraries (requests, pandas).
        Set the EMAIL variable to your email address.
        If you have an OpenAlex API key, add it to the API_KEY variable.
    Configure Search Parameters:
        Adjust START_YEAR and END_YEAR to define the range of years to search.
        Review and modify the search_terms in the get_raw_affiliations function if needed.
    Prepare Filter Strings:
        Create a file named filter_strings.txt in the same directory as the script.
        Add any strings you want to use for filtering affiliations, one per line.
    Run the Script:
        Open a terminal or command prompt.
        Navigate to the directory containing the script.
        Run the script using Python: python script_name.py
    Review Results:
        The script will display progress information and statistics in the console.
        Check the generated CSV files for detailed results:
            potential_kth_affiliations_[YEAR-RANGE]_[DATE].csv: All potential KTH affiliations.
            filtered_affiliations_[DATE].csv: Filtered affiliations based on your filter strings.
            all_potential_kth_affiliations_[YEAR-RANGE]_[DATE].csv: Comprehensive list of all potential affiliations.
    Iterate and Refine:
        Review the results and adjust the search terms or filter strings as needed.
        Re-run the script to refine your results.

Notes

    The script uses rate limiting (1-second delay between API calls) to avoid overloading the OpenAlex API.
    Large date ranges may take a significant amount of time to process.
    Ensure you comply with OpenAlex's terms of service and usage policies.

text

This markdown file provides an overview of the script's structure and functionality, along with instructions on how to use it. You can save this as a README.md file in the same directory as your script for easy reference.
