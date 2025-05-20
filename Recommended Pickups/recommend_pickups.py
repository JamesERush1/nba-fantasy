import pandas as pd
import numpy as np
import os
import sys
import argparse

def load_rankings():
    try:
        # Load the rankings file
        rankings_file = 'nba_fantasy_rankings_three_metrics.csv'
        if not os.path.exists(rankings_file):
            print(f"Error: Rankings file '{rankings_file}' not found.")
            print("Run fantasy_ranking.py first to generate rankings.")
            sys.exit(1)
            
        rankings_df = pd.read_csv(rankings_file)
        print(f"Loaded rankings for {len(rankings_df)} players")
        return rankings_df
    except Exception as e:
        print(f"Error loading rankings: {str(e)}")
        sys.exit(1)

def load_available_players(filename=None):
    """
    Load a list of available players from a CSV file.
    If no file provided, prompt the user to enter players manually.
    """
    if filename and os.path.exists(filename):
        try:
            available_df = pd.read_csv(filename)
            print(f"Loaded {len(available_df)} available players from {filename}")
            return available_df['PLAYER_NAME'].tolist()
        except Exception as e:
            print(f"Error loading available players: {str(e)}")
            print("Falling back to manual entry...")
    
    # Manual entry if no file or error loading
    print("\nEnter available players (one per line, press Enter twice when done):")
    players = []
    while True:
        player = input().strip()
        if not player:
            break
        players.append(player)
    
    return players

def find_best_pickups(rankings_df, available_players, top_n=10):
    """
    Find the best available players based on rankings.
    """
    # Create a case-insensitive player name for matching
    rankings_df['PLAYER_NAME_LOWER'] = rankings_df['PLAYER_NAME'].str.lower()
    
    # Convert available players to lowercase for matching
    available_players_lower = [p.lower() for p in available_players]
    
    # Filter rankings to only include available players
    available_df = rankings_df[rankings_df['PLAYER_NAME_LOWER'].isin(available_players_lower)]
    
    # Sort by ranking score
    recommendations = available_df.sort_values('FANTASY_RANK_PERCENTILE', ascending=False).head(top_n)
    
    return recommendations[['PLAYER_NAME', 'TEAM_ABBREVIATION', 
                           'FANTASY_RANK_PERCENTILE', 'FANTASY_POINTS_PER_MIN', 
                           'PCT_MINUTES_PLAYED', 'PCT_GAMES_PLAYED']]

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='NBA Fantasy Basketball Pickup Recommendations')
    parser.add_argument('--file', '-f', help='Path to CSV file with available players')
    parser.add_argument('--top', '-t', type=int, default=10, help='Number of top recommendations to show')
    args = parser.parse_args()
    
    print("NBA Fantasy Basketball Pickup Recommendations")
    print("=============================================")
    
    # Load rankings
    rankings_df = load_rankings()
    
    # Get available players
    if args.file:
        available_players = load_available_players(args.file)
    else:
        # Ask if user has a CSV of available players or wants to enter manually
        use_csv = input("\nDo you have a CSV file with available players? (y/n): ").lower() == 'y'
        
        if use_csv:
            csv_file = input("Enter the path to your CSV file: ").strip()
            available_players = load_available_players(csv_file)
        else:
            available_players = load_available_players()
    
    if not available_players:
        print("No available players provided. Exiting.")
        return
    
    print(f"\nAnalyzing {len(available_players)} available players...")
    
    # Get pickup recommendations
    recommendations = find_best_pickups(rankings_df, available_players, args.top)
    
    # Display recommendations
    print("\nTop Recommended Pickups:")
    print("------------------------")
    for i, (_, player) in enumerate(recommendations.iterrows(), 1):
        print(f"{i}. {player['PLAYER_NAME']} ({player['TEAM_ABBREVIATION']})")
        print(f"   Ranking: {player['FANTASY_RANK_PERCENTILE']:.1f} percentile")
        print(f"   Fantasy Points Per Min: {player['FANTASY_POINTS_PER_MIN']:.2f}")
        print(f"   % Minutes Played: {player['PCT_MINUTES_PLAYED']:.1f}%")
        print(f"   % Games Played: {player['PCT_GAMES_PLAYED']:.1f}%")
        print()

if __name__ == "__main__":
    main() 