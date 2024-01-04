import base64;
import json

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver


def remove_name_extension(name):
    """
    Remove specific name extensions from a given name.
    """
    suffixes_to_remove = ["Jr.", "Sr.", "II", "III", "IV", "Ph.D."]  # Add more suffixes if needed
    cleaned_name = name.replace("'", "").replace("-", "")
    for suffix in suffixes_to_remove:
        cleaned_name = cleaned_name.replace(suffix, "").strip()
    return cleaned_name


# Function to scrape and save data
def scrape_and_save_data(base_url):
    # Set up the web driver (make sure to specify the path to your browser driver)
    driver = webdriver.Chrome()

    decoded_url = base64.b64decode(base_url).decode()
    print("Opening URL", decoded_url)
    # Open the initial page
    driver.get(decoded_url)

    # Adjust the locator based on your HTML structure
    table_locator = (By.TAG_NAME, 'table')

    # Wait for the presence of the table
    table = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(table_locator)
    )

    dfdata = []
    for request in list(driver.requests):
        if request.response and 'players.php' in request.url:
            print(
                request.url,
                request.response.status_code,
                request.response.headers['Content-Type'],
                flush=True
            )

            driver.get(request.url)

            # Wait for at least one <pre> element to load (adjust the timeout as needed)
            wait = WebDriverWait(driver, 60)
            elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'pre')))

            # Initialize an empty list to store the text content of all <pre> elements
            json_data_list = []

            # Extract the text content of all <pre> elements
            for element in elements:
                json_data_list.append(element.text)

            # Attempt to parse the extracted text as JSON
            try:
                # Combine the text content of all <pre> elements into a single JSON string
                combined_json_data = ''.join(json_data_list)

                data = json.loads(combined_json_data)

                for d in data:
                    if d['injuryStatus'] != 'OUT':
                        name = remove_name_extension(d['firstName'] + " " + d['lastName'])
                        pos = d['rotoPos']
                        team = d['team']['abbr']
                        fp_proj = float(d['pts'])
                        print(name, pos, team, fp_proj, flush=True)
                        player = {"PLAYER": name, "POS": pos, "TEAM": team, "FP": fp_proj}
                        dfdata.append(player)

            except json.JSONDecodeError:
                print("The extracted text is not valid JSON.")

    df = pd.DataFrame(dfdata)

    df = df.rename(columns={"PLAYER": "Name", "POS": "Position", "TEAM": "Team", "FP": "Projection"})

    df = df.loc[:, ['Name', 'Position', 'Team', 'Projection']]
    df['Projection'] = df['Projection'].astype(float)
    df = df.sort_values(by=['Projection'], ascending=False)
    # Close the browser
    driver.quit()

    return df;


def get_projections():
    # URLs and output folder
    nba_url = "aHR0cHM6Ly93d3cucm90b3dpcmUuY29tL2RhaWx5L25iYS9vcHRpbWl6ZXIucGhw="

    # Scraping and saving data for NBA, MLB, and NFL
    return scrape_and_save_data(nba_url)
