import requests
import json
import pandas as pd
import time
import os
import sys
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='NBA Fantasy Basketball Data Tool')
parser.add_argument('--sheets', action='store_true', help='Upload data directly to Google Sheets')
parser.add_argument('--worksheet', type=str, default='NBA_Fantasy_Data', help='Name of the worksheet for Google Sheets upload')
parser.add_argument('--no-csv', action='store_true', help='Skip saving data to CSV file')
args = parser.parse_args()

# Google Sheet configuration
SHEET_ID = '1NythdZUtn3IK9897ig8zGIXpA446z1rSMIUhemY6dhs'
CREDENTIALS_FILE = 'service_account.json'

def upload_df_to_google_sheets(df, worksheet_name=None):
    """Upload a dataframe directly to Google Sheets"""
    print("\nUploading data to Google Sheets...")
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Error: Credentials file '{CREDENTIALS_FILE}' not found in current directory.")
        print(f"Make sure 'service_account.json' is in: {os.getcwd()}")
        return False
    
    # Define the required scopes
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Get worksheet name if not provided
    if worksheet_name is None:
        worksheet_name = input("Enter worksheet name (or press Enter for default 'NBA_Fantasy_Data'): ")
        if not worksheet_name.strip():
            worksheet_name = "NBA_Fantasy_Data"
    
    try:
        # Authenticate using the service account credentials
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_FILE, 
            scopes=scopes
        )
        
        # Create a client to interact with Google Sheets API
        client = gspread.authorize(credentials)
        
        # Open the spreadsheet by its ID
        spreadsheet = client.open_by_key(SHEET_ID)
        print(f"Successfully connected to spreadsheet: {spreadsheet.title}")
        
        # Try to find existing worksheet or create new one
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"Using existing worksheet: {worksheet_name}")
            # Clear existing content
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name, 
                rows=max(100, len(df) + 10), 
                cols=max(20, len(df.columns) + 5)
            )
            print(f"Created new worksheet: {worksheet_name}")
        
        # Upload the data
        set_with_dataframe(
            worksheet=worksheet,
            dataframe=df,
            include_index=False,
            include_column_header=True,
            resize=True
        )
        
        print(f"Successfully uploaded data to worksheet '{worksheet_name}'")
        print(f"Access your data at: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={worksheet.id}")
        
        return True
        
    except Exception as e:
        print(f"Error uploading to Google Sheets: {e}")
        return False

url = "https://stats.nba.com/stats/leaguedashplayerstats"
params = {
    "College": "",
    "Conference": "",
    "Country": "",
    "DateFrom": "",
    "DateTo": "",
    "Division": "",
    "DraftPick": "",
    "DraftYear": "",
    "GameScope": "",
    "GameSegment": "",
    "Height": "",
    "LastNGames": "0",
    "LeagueID": "00",
    "Location": "",
    "MeasureType": "Base",
    "Month": "0",
    "OpponentTeamID": "0",
    "Outcome": "",
    "PORound": "0",
    "PaceAdjust": "N",
    "PerMode": "Totals",
    "Period": "0",
    "PlayerExperience": "",
    "PlayerPosition": "",
    "PlusMinus": "N",
    "Rank": "N",
    "SeasonSegment": "",
    "SeasonType": "Regular Season",
    "ShotClockRange": "",
    "StarterBench": "",
    "TeamID": "0",
    "VsConference": "",
    "VsDivision": "",
    "Weight": ""
}

request_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/"
}

# List of seasons to fetch
seasons = ["2023-24", "2024-25"]

all_data = []

for season in seasons:
    params["Season"] = season
    try:
        response = requests.get(url, headers=request_headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data['resultSets'][0]
            column_headers = results['headers']
            rows = results['rowSet']
            df = pd.DataFrame(rows, columns=column_headers)
            
            # Add a SEASON column to track which season the data belongs to
            df['SEASON'] = season
            
            all_data.append(df)
            print(f"Successfully fetched data for season {season}")
        else:
            print(f"Error fetching data for season {season}: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while fetching data for season {season}: {str(e)}")

# Concatenate all data into a single DataFrame if we have data
if all_data:
    try:
        final_df = pd.concat(all_data, ignore_index=True)
        print(f"Combined data: {len(final_df)} rows")
        
        # Only keep columns directly related to fantasy scoring
        # Player identification columns
        id_columns = ['SEASON', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN']
        
        # Stats that contribute to fantasy scoring
        stat_columns = [
            'FGM', 'FGA',      # Field goals: +1 for makes, -1 for attempts
            'FTM', 'FTA',      # Free throws: +1 for makes, -1 for attempts
            'FG3M',            # Three pointers: +1
            'OREB',            # Offensive rebounds: +0.5
            'REB',             # Total rebounds: +1
            'AST',             # Assists: +1
            'STL',             # Steals: +1.5
            'BLK',             # Blocks: +1.5
            'TOV',             # Turnovers: -1
            'PF',              # Personal fouls: -1
            'PTS'              # Points: +1
        ]
        
        # Select only columns that exist in the data
        existing_id_columns = [col for col in id_columns if col in final_df.columns]
        existing_stat_columns = [col for col in stat_columns if col in final_df.columns]
        
        fantasy_df = final_df[existing_id_columns + existing_stat_columns].copy()
        
        # Calculate fantasy points based on the scoring system
        fantasy_df['FANTASY_POINTS'] = (
            fantasy_df['FGM'] * 1 +
            fantasy_df['FGA'] * -1 + 
            fantasy_df['FTM'] * 1 +
            fantasy_df['FTA'] * -1 + 
            fantasy_df['FG3M'] * 1 +
            fantasy_df['OREB'] * 0.5 +
            fantasy_df['REB'] * 1 +
            fantasy_df['AST'] * 1 +
            fantasy_df['STL'] * 1.5 +
            fantasy_df['BLK'] * 1.5 +
            fantasy_df['TOV'] * -1 +
            fantasy_df['PF'] * -1 +
            fantasy_df['PTS'] * 1
        )
            
        # Calculate additional metrics
        fantasy_df['AVG_FANTASY_PPG'] = fantasy_df['FANTASY_POINTS'] / fantasy_df['GP']
        
        # Assuming 82 games in a season for NBA
        total_games_in_season = 82
        
        # Calculate percentage of games played - a critical metric for fantasy value
        # This indicates a player's durability and availability throughout the season
        fantasy_df['PCT_GAMES_PLAYED'] = (fantasy_df['GP'] / total_games_in_season) * 100
        
        # Add minutes stats
        fantasy_df['AVG_MINUTES'] = fantasy_df['MIN'] / fantasy_df['GP']
        
        # Assuming 48 minutes per game times 82 games
        total_minutes_possible = 48 * total_games_in_season
        fantasy_df['PCT_MINUTES_PLAYED'] = (fantasy_df['MIN'] / total_minutes_possible) * 100
        
        # Calculate fantasy points per minute
        fantasy_df['FANTASY_POINTS_PER_MIN'] = fantasy_df['FANTASY_POINTS'] / fantasy_df['MIN']
        
        # Replace any NaN values with 0
        fantasy_df = fantasy_df.fillna(0)
        
        # Round decimal values for readability
        for col in ['FANTASY_POINTS', 'AVG_FANTASY_PPG', 'PCT_GAMES_PLAYED', 
                   'AVG_MINUTES', 'PCT_MINUTES_PLAYED', 'FANTASY_POINTS_PER_MIN']:
            if col in fantasy_df.columns:
                fantasy_df[col] = fantasy_df[col].round(2)
        
        # Sort by fantasy points in descending order
        fantasy_df = fantasy_df.sort_values('FANTASY_POINTS', ascending=False)
        
        # Final columns in the desired order
        final_columns = [
            # Player info
            'SEASON', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 
            # Game stats
            'GP', 'PCT_GAMES_PLAYED', 'MIN', 'AVG_MINUTES', 'PCT_MINUTES_PLAYED',
            # Fantasy metrics
            'FANTASY_POINTS', 'AVG_FANTASY_PPG', 'FANTASY_POINTS_PER_MIN',
            # Box score stats that contribute to fantasy
            'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF',
            'FGM', 'FGA', 'FTM', 'FTA', 'FG3M', 'OREB'
        ]
        
        # Only keep columns that exist
        final_columns = [col for col in final_columns if col in fantasy_df.columns]
        fantasy_df = fantasy_df[final_columns]
        
        print(f"Fantasy data prepared: {len(fantasy_df)} players")
        print("Columns in final dataset:")
        print(fantasy_df.columns.tolist())
        print("\nPreview of top players:")
        print(fantasy_df[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'PCT_GAMES_PLAYED', 'FANTASY_POINTS']].head())
        
        # Print summary of key metrics for fantasy evaluation
        print("\nKey metrics for fantasy evaluation:")
        print(f"1. PCT_GAMES_PLAYED: Shows what percentage of the season's games a player participated in")
        print(f"2. PCT_MINUTES_PLAYED: Shows what percentage of total possible minutes a player played")
        print(f"3. FANTASY_POINTS_PER_MIN: Shows efficiency when on the court")
        
        # Save to CSV (unless --no-csv flag is used)
        if not args.no_csv:
            fantasy_df.to_csv('nba_fantasy_stats_new.csv', index=False)
            print("Fantasy data saved to nba_fantasy_stats_new.csv")
        
        # Upload to Google Sheets if requested via command line or prompt user
        if args.sheets:
            upload_df_to_google_sheets(fantasy_df, args.worksheet)
        else:
            upload_to_sheets = input("\nDo you want to upload this data to Google Sheets? (y/n): ").lower() == 'y'
            if upload_to_sheets:
                upload_df_to_google_sheets(fantasy_df)
            
    except Exception as e:
        print(f"Error while processing data: {str(e)}")
else:
    print("No data was fetched. Cannot create DataFrame.") 