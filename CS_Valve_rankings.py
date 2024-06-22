import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz
import re

# URLs for the leaderboard data
LEADERBOARD_URLS = {
    "Global": "https://raw.githubusercontent.com/ValveSoftware/counter-strike_regional_standings/main/standings_global.md",
    "Americas": "https://raw.githubusercontent.com/ValveSoftware/counter-strike_regional_standings/main/standings_americas.md",
    "Asia": "https://raw.githubusercontent.com/ValveSoftware/counter-strike_regional_standings/main/standings_asia.md",
    "Europe": "https://raw.githubusercontent.com/ValveSoftware/counter-strike_regional_standings/main/standings_europe.md"
}

@st.cache_data(ttl=24*60*60)  # Cache for 24 hours
def fetch_leaderboard_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        st.error(f"Failed to fetch data from {url}")
        return None

def parse_markdown_table(markdown_text):
    lines = markdown_text.strip().split('\n')
    
    # Extract the timestamp
    timestamp_match = re.search(r"(?:Standings|Regional Standings for \w+) as of (\d{4}-\d{2}-\d{2})", lines[0])
    timestamp = timestamp_match.group(1) if timestamp_match else "Unknown"
    
    # Find the header row
    header_index = next((i for i, line in enumerate(lines) if line.startswith('| Standing |')), None)
    
    if header_index is None:
        raise ValueError("Could not find the header row in the Markdown table.")
    
    # Extract headers
    headers = [header.strip() for header in lines[header_index].split('|')[1:-1]]
    headers[-1] = "Details"  # Name the last column "Details"
    
    # Extract data
    data = []
    for line in lines[header_index+2:]:  # Skip the separator line
        if line.startswith('|') and '|' in line:
            row = [cell.strip() for cell in line.split('|')[1:-1]]
            if row and len(row) == len(headers):
                # Convert the last column to a clickable link
                detail_link = row[-1]
                row[-1] = f"https://github.com/ValveSoftware/counter-strike_regional_standings/blob/main/{detail_link[detail_link.index('(') + 1:-1]}"
                data.append(row)
    
    if not data:
        raise ValueError("No data rows found in the Markdown table.")
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=headers)
    
    return df, timestamp

def display_leaderboard(leaderboard_name):
    markdown_data = fetch_leaderboard_data(LEADERBOARD_URLS[leaderboard_name])
    if markdown_data:
        try:
            df, timestamp = parse_markdown_table(markdown_data)
            
            # Display the full table
            st.dataframe(df, height=35*len(df)+38, use_container_width=True, hide_index=True, 
                         column_config={"Details": st.column_config.LinkColumn(display_text="Details")})

            # Display the timestamp from the Markdown file
            st.markdown(f"<p style='text-align: right; color: gray; font-size: small;'>Standings as of: {timestamp}</p>", unsafe_allow_html=True)

            # Display last updated time (when our app fetched the data)
            pst = pytz.timezone('US/Pacific')
            last_updated = datetime.now(pst).strftime("%Y-%m-%d %H:%M:%S %Z")
            st.markdown(f"<p style='text-align: right; color: gray; font-size: small;'>Last fetched: {last_updated}</p>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error parsing the leaderboard data: {str(e)}")
            st.text("Raw markdown data (first 1000 characters):")
            st.code(markdown_data[:1000], language="markdown")
            st.text("Last 1000 characters of markdown data:")
            st.code(markdown_data[-1000:], language="markdown")

def main():
    st.set_page_config(layout="wide")  # Use wide layout for more space
    st.title("Counter-Strike Regional Standings")

    # Create tabs for each leaderboard
    tabs = st.tabs(list(LEADERBOARD_URLS.keys()))

    # Display the appropriate leaderboard based on the selected tab
    for tab, leaderboard_name in zip(tabs, LEADERBOARD_URLS.keys()):
        with tab:
            display_leaderboard(leaderboard_name)

if __name__ == "__main__":
    main()