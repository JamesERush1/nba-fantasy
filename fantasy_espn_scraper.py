import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def initialize_driver():
    """Initialize and return a Chrome webdriver with appropriate options"""
    chrome_options = Options()
    # Uncomment the line below if you want to run in headless mode (no UI)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    
    # Initialize Chrome webdriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def login_to_espn(driver, username, password):
    """Log in to ESPN Fantasy Basketball"""
    # Navigate to the login page
    driver.get("https://www.espn.com/login")
    
    try:
        # Wait for the login form to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "oneid-iframe"))
        )
        
        # Switch to the login iframe
        iframe = driver.find_element(By.ID, "oneid-iframe")
        driver.switch_to.frame(iframe)
        
        # Enter login credentials
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "InputLoginValue"))
        )
        
        username_field = driver.find_element(By.ID, "InputLoginValue")
        password_field = driver.find_element(By.ID, "InputPassword")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Submit the form
        login_button = driver.find_element(By.ID, "BtnSubmit")
        login_button.click()
        
        # Wait for login to complete and return to main content
        WebDriverWait(driver, 10).until(
            EC.url_contains("espn.com")
        )
        
        driver.switch_to.default_content()
        print("Login successful!")
        return True
        
    except TimeoutException:
        print("Login failed - timeout waiting for elements.")
        return False
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

def scrape_available_players(driver, league_id):
    """Scrape available players from the ESPN Fantasy Basketball free agents page"""
    # Navigate to the free agents page
    url = f"https://fantasy.espn.com/basketball/players/add?leagueId={league_id}"
    driver.get(url)
    
    # Wait for the player table to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Table__TBODY"))
        )
    except TimeoutException:
        print("Timeout waiting for player table to load.")
        return []
    
    # Let the page fully load (some elements load dynamically)
    time.sleep(5)
    
    # Get all player rows
    player_rows = driver.find_elements(By.CSS_SELECTOR, ".Table__TBODY tr")
    
    # Extract player data
    available_players = []
    for row in player_rows:
        try:
            # Extract name, team, and position
            name_element = row.find_element(By.CSS_SELECTOR, ".player-column__athlete")
            name = name_element.text.strip()
            
            # Extract team and position
            team_pos_element = row.find_element(By.CSS_SELECTOR, ".player-column__position")
            team_pos_text = team_pos_element.text.strip()
            
            # Parse team and position (format is usually "TEAM - POS")
            if " - " in team_pos_text:
                team, position = team_pos_text.split(" - ", 1)
            else:
                team = team_pos_text
                position = "Unknown"
            
            # Add to our list
            available_players.append({
                "PLAYER_NAME": name,
                "TEAM_ABBREVIATION": team,
                "POSITION": position
            })
            
        except Exception as e:
            print(f"Error extracting player data: {str(e)}")
            continue
    
    print(f"Scraped {len(available_players)} available players.")
    return available_players

def normalize_player_name(name):
    """Normalize player names for better matching between datasets"""
    # Convert to lowercase
    name = name.lower()
    
    # Handle common name variations
    name = name.replace(".", "")  # Remove periods
    name = name.replace("'", "")  # Remove apostrophes
    name = name.replace("-", " ")  # Replace hyphens with spaces
    
    # Handle suffixes
    suffixes = [" jr", " sr", " ii", " iii", " iv"]
    for suffix in suffixes:
        if suffix in name:
            name = name.replace(suffix, "")
    
    # Remove extra spaces and trim
    name = " ".join(name.split())
    
    return name

def match_player_with_rankings(available_players, rankings_file):
    """Match available players with our fantasy rankings"""
    # Load our rankings data
    rankings = pd.read_csv(rankings_file)
    
    # Create a normalized version of player names in both datasets for matching
    rankings['NORMALIZED_NAME'] = rankings['PLAYER_NAME'].apply(normalize_player_name)
    
    for player in available_players:
        player['NORMALIZED_NAME'] = normalize_player_name(player['PLAYER_NAME'])
    
    # Convert available players to DataFrame for easier matching
    available_df = pd.DataFrame(available_players)
    
    # Merge the datasets based on normalized names
    merged = pd.merge(
        available_df, 
        rankings[['NORMALIZED_NAME', 'PLAYER_NAME', 'FANTASY_RANK_SCORE', 'FANTASY_RANK_PERCENTILE', 
                 'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED']], 
        on='NORMALIZED_NAME', 
        how='left',
        suffixes=('_ESPN', '_RANKINGS')
    )
    
    # Handle players not found in our rankings
    missing_players = merged[merged['FANTASY_RANK_SCORE'].isna()]
    matched_players = merged[~merged['FANTASY_RANK_SCORE'].isna()]
    
    print(f"Successfully matched {len(matched_players)} players with our rankings.")
    print(f"{len(missing_players)} players could not be matched.")
    
    # Sort matched players by our ranking score (descending)
    matched_players = matched_players.sort_values('FANTASY_RANK_SCORE', ascending=False)
    
    return matched_players, missing_players

def recommend_pickups(matched_players, top_n=10):
    """Generate pickup recommendations based on our rankings"""
    if len(matched_players) == 0:
        print("No available players matched with our rankings.")
        return pd.DataFrame()
    
    # Select top N players
    top_pickups = matched_players.head(top_n)
    
    # Create a recommendations DataFrame with relevant columns
    recommendations = top_pickups[[
        'PLAYER_NAME_ESPN', 'TEAM_ABBREVIATION', 'POSITION',
        'FANTASY_RANK_PERCENTILE', 'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED'
    ]].copy()
    
    # Rename columns for clarity
    recommendations = recommendations.rename(columns={
        'PLAYER_NAME_ESPN': 'PLAYER_NAME',
        'FANTASY_RANK_PERCENTILE': 'RANK_PERCENTILE'
    })
    
    return recommendations

def main():
    # ESPN account credentials and league ID
    username = input("Enter your ESPN username: ")
    password = input("Enter your ESPN password: ")
    league_id = input("Enter your league ID (default: 1609818238): ") or "1609818238"
    
    # Path to our rankings file
    rankings_file = "nba_fantasy_rankings_original.csv"
    if not os.path.exists(rankings_file):
        print(f"Error: Rankings file '{rankings_file}' not found.")
        print("Please run fantasy_ranking.py first to generate rankings.")
        return
    
    # Initialize webdriver
    print("Initializing Chrome webdriver...")
    driver = initialize_driver()
    
    try:
        # Login to ESPN (uncomment when ready to use with real credentials)
        #login_successful = login_to_espn(driver, username, password)
        #if not login_successful:
        #    print("Failed to log in. Exiting.")
        #    return
        
        # For testing without login, just navigate directly to the page
        print("Navigating to free agents page (note: actual login is commented out for testing)...")
        
        # Scrape available players
        available_players = scrape_available_players(driver, league_id)
        
        if not available_players:
            print("No available players found or scraping failed.")
            return
        
        # Match with rankings and get recommendations
        matched_players, missing_players = match_player_with_rankings(available_players, rankings_file)
        recommendations = recommend_pickups(matched_players)
        
        # Save recommendations to CSV
        if not recommendations.empty:
            recommendations.to_csv("fantasy_pickup_recommendations_original.csv", index=False)
            print("\nTop Recommended Pickups (based on minutes played & fantasy points per minute):")
            print(recommendations.to_string(index=False))
            print("\nRecommendations saved to fantasy_pickup_recommendations_original.csv")
        
        # Save missing players to CSV for reference
        if not missing_players.empty:
            missing_players[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'POSITION']].to_csv(
                "unmatched_available_players.csv", index=False
            )
            print(f"List of {len(missing_players)} unmatched players saved to unmatched_available_players.csv")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        # Close the browser
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main() 