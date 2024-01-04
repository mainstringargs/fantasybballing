import base64;
import os

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Function to scrape and save data
def scrape_and_save_data(base_url):
    # Initialize empty lists to store data
    player_list, team_list, stat_list, line_list, bet_list, win_percent_list = [], [], [], [], [], []

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

    # Find all rows within the table
    rows = table.find_elements(By.TAG_NAME, 'tr')

    print("Num rows", len(rows))
    headers = []
    # Iterate through the rows of the table
    i = 0;

    data = []

    for row in rows:
        # print("row.text",row.text)
        tds = row.find_elements(By.TAG_NAME, 'td')
        # print("tds", len(tds),tds)

        if i == 0:
            headers = row.text.split()
        else:

            player = {}
            for x in range(0, len(tds)):
                player[headers[x]] = tds[x].text
                # print(x,headers[x],tds[x].text)

            data.append(player)

        i = i + 1

    df = pd.DataFrame(data)

    # 'Name','Position','Team','Projection'

    # df = df.rename(columns={"PLAYER": "Name", "POS": "Position", "TEAM": "Team", "FP": "Projection"})
    df = df.rename(columns={"PLAYER": "Name", "POS": "Position", "TEAM": "Team", "DK": "Projection"})
    # df.rename(columns={"PLAYER": "Name", "POS": "Position", "TEAM": "Team", "FD": "Projection"})

    df = df.loc[:, ['Name', 'Position', 'Team', 'Projection']]
    df['Projection'] = df['Projection'].astype(float)

    df = df.sort_values(by=['Projection'], ascending=False)

    # Generate a filename with the current date
    # current_datetime = time.strftime("%Y-%m-%d_%H%M%S")
    #  file_name = os.path.join(output_folder, f"{sport}_data_{current_datetime}.csv")

    # Save the data to a CSV file
    # df.to_csv(file_name, index=False)

    # Close the browser
    driver.quit()

    return df;


def get_projections():
    # URLs and output folder
    nba_url = "aHR0cHM6Ly93d3cuc3BvcnRzbGluZS5jb20vbmJhL2V4cGVydC1wcm9qZWN0aW9ucy9zaW11bGF0aW9uLw=="

    # Scraping and saving data for NBA, MLB, and NFL
    return scrape_and_save_data(nba_url)
