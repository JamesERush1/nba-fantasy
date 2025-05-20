import pandas as pd
import numpy as np
from scipy import stats

# Load the fantasy data
try:
    df = pd.read_csv(r'C:\fantasy\nba-fantasy\nba_fantasy_stats_new.csv')
except FileNotFoundError:
    print("Error: File 'nba_fantasy_stats_new.csv' not found.")
    exit()

# Group data by player to aggregate across seasons
player_groups = df.groupby('PLAYER_NAME')

# Create aggregated dataframe
aggregated_data = []
for player, data in player_groups:
    # Calculate weighted averages based on games played
    total_gp = data['GP'].sum()
    
    if total_gp >= 20:  # Apply minimum games filter to aggregated data
        avg_minutes = np.average(data['AVG_MINUTES'], weights=data['GP'])
        
        if avg_minutes >= 10:  # Apply minimum minutes filter to aggregated data
            # Aggregate data across seasons
            player_data = {
                'PLAYER_NAME': player,
                'TEAM_ABBREVIATION': data['TEAM_ABBREVIATION'].iloc[-1],  # Most recent team
                'GP': total_gp,
                'AVG_MINUTES': avg_minutes,
                'FANTASY_POINTS': data['FANTASY_POINTS'].sum(),
                'AVG_FANTASY_PPG': np.average(data['AVG_FANTASY_PPG'], weights=data['GP']),
                'FANTASY_POINTS_PER_MIN': np.average(data['FANTASY_POINTS_PER_MIN'], weights=data['GP']),
                'PCT_MINUTES_PLAYED': np.average(data['PCT_MINUTES_PLAYED'], weights=data['GP']),
                'PCT_GAMES_PLAYED': np.average(data['PCT_GAMES_PLAYED'], weights=data['GP'])
            }
            aggregated_data.append(player_data)

# Create new dataframe with aggregated stats
df_filtered = pd.DataFrame(aggregated_data)

print(f"Total players in original data: {len(df)}")
print(f"Players after aggregating and filtering: {len(df_filtered)}")

# Analyze correlation between key metrics and total fantasy points
print("\nCorrelation with total FANTASY_POINTS:")
correlations = {
    'AVG_FANTASY_PPG': df_filtered['AVG_FANTASY_PPG'].corr(df_filtered['FANTASY_POINTS']),
    'PCT_MINUTES_PLAYED': df_filtered['PCT_MINUTES_PLAYED'].corr(df_filtered['FANTASY_POINTS']),
    'PCT_GAMES_PLAYED': df_filtered['PCT_GAMES_PLAYED'].corr(df_filtered['FANTASY_POINTS']),
    'AVG_MINUTES': df_filtered['AVG_MINUTES'].corr(df_filtered['FANTASY_POINTS']),
    'GP': df_filtered['GP'].corr(df_filtered['FANTASY_POINTS']),
    'FANTASY_POINTS_PER_MIN': df_filtered['FANTASY_POINTS_PER_MIN'].corr(df_filtered['FANTASY_POINTS'])
}

for metric, corr in sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True):
    print(f"{metric}: {corr:.4f}")

# Check for correlation between our key metrics
print("\nCorrelations between key metrics:")
print(f"% Minutes vs Fantasy Points Per Min: {df_filtered['PCT_MINUTES_PLAYED'].corr(df_filtered['FANTASY_POINTS_PER_MIN']):.4f}")
print(f"% Games Played vs % Minutes: {df_filtered['PCT_GAMES_PLAYED'].corr(df_filtered['PCT_MINUTES_PLAYED']):.4f}")
print(f"% Games Played vs Fantasy Points Per Min: {df_filtered['PCT_GAMES_PLAYED'].corr(df_filtered['FANTASY_POINTS_PER_MIN']):.4f}")

# Develop a combined ranking metric
# Normalize both metrics to a 0-1 scale
df_filtered['NORM_MINUTES_PCT'] = (df_filtered['PCT_MINUTES_PLAYED'] - df_filtered['PCT_MINUTES_PLAYED'].min()) / \
                                 (df_filtered['PCT_MINUTES_PLAYED'].max() - df_filtered['PCT_MINUTES_PLAYED'].min())

df_filtered['NORM_FANTASY_PER_MIN'] = (df_filtered['FANTASY_POINTS_PER_MIN'] - df_filtered['FANTASY_POINTS_PER_MIN'].min()) / \
                                     (df_filtered['FANTASY_POINTS_PER_MIN'].max() - df_filtered['FANTASY_POINTS_PER_MIN'].min())

df_filtered['NORM_GAMES_PCT'] = (df_filtered['PCT_GAMES_PLAYED'] - df_filtered['PCT_GAMES_PLAYED'].min()) / \
                               (df_filtered['PCT_GAMES_PLAYED'].max() - df_filtered['PCT_GAMES_PLAYED'].min())

# Try different weightings to find optimal combination
weights = []
for w_min in [0.2, 0.3, 0.4, 0.5]:
    for w_fpm in [0.2, 0.3, 0.4, 0.5]:
        for w_gp in [0.2, 0.3, 0.4, 0.5]:
            if abs(w_min + w_fpm + w_gp - 1.0) < 0.001:  # Ensure weights sum to 1
                weights.append((w_min, w_fpm, w_gp))

correlations_by_weight = {}

print("\nTesting different weight combinations:")
print("---------------------------------------------------------------")
print("Weight for % Minutes | Weight for Points/Min | Weight for % Games | Correlation")
print("---------------------------------------------------------------")

for w_min, w_fpm, w_gp in weights:
    # Create weighted score
    df_filtered[f'WEIGHTED_SCORE_{w_min}_{w_fpm}_{w_gp}'] = (
        w_min * df_filtered['NORM_MINUTES_PCT'] + 
        w_fpm * df_filtered['NORM_FANTASY_PER_MIN'] +
        w_gp * df_filtered['NORM_GAMES_PCT']
    )
    
    # Check correlation with total fantasy points
    corr = df_filtered[f'WEIGHTED_SCORE_{w_min}_{w_fpm}_{w_gp}'].corr(df_filtered['FANTASY_POINTS'])
    correlations_by_weight[(w_min, w_fpm, w_gp)] = corr
    print(f"      {w_min:.2f}         |        {w_fpm:.2f}         |       {w_gp:.2f}       |   {corr:.4f}")

# Find best weighting
best_weights = max(correlations_by_weight.items(), key=lambda x: x[1])
w_min_best, w_fpm_best, w_gp_best = best_weights[0]
print("\n---------------------------------------------------------------")
print(f"Best weights: {w_min_best:.2f} for % minutes, {w_fpm_best:.2f} for points per minute, {w_gp_best:.2f} for % games played")
print(f"Best correlation: {best_weights[1]:.4f}")

# Explain the meaning of the weights
print("\nWhat these weights mean:")
print(f"- % Minutes Played ({w_min_best:.2f}): How much of all possible minutes a player plays")
print(f"- Fantasy Points Per Minute ({w_fpm_best:.2f}): How efficient a player is when on the court")
print(f"- % Games Played ({w_gp_best:.2f}): How reliable a player is in terms of availability")
print("\nThese weights create a balanced ranking that accounts for player efficiency,")
print("playing time, and durability - all key factors for fantasy basketball success.")

# Create final ranking score using the best weights
df_filtered['FANTASY_RANK_SCORE'] = (
    w_min_best * df_filtered['NORM_MINUTES_PCT'] + 
    w_fpm_best * df_filtered['NORM_FANTASY_PER_MIN'] +
    w_gp_best * df_filtered['NORM_GAMES_PCT']
)

# Calculate percentile rank (0-100 scale, higher is better)
df_filtered['FANTASY_RANK_PERCENTILE'] = df_filtered['FANTASY_RANK_SCORE'].rank(pct=True) * 100

# Sort by the ranking score
df_ranked = df_filtered.sort_values('FANTASY_RANK_SCORE', ascending=False)

# Display top players (now aggregated across seasons)
print("\nTop 15 players (aggregated across seasons):")
top_players = df_ranked.head(15)
print(top_players[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'PCT_GAMES_PLAYED', 'AVG_MINUTES', 
                   'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED', 'FANTASY_RANK_SCORE', 
                   'FANTASY_RANK_PERCENTILE', 'FANTASY_POINTS']])

# Save detailed rankings to CSV
df_ranking_output = df_ranked[['PLAYER_NAME', 'TEAM_ABBREVIATION', 
                             'FANTASY_RANK_SCORE', 'FANTASY_RANK_PERCENTILE',
                             'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED', 'PCT_GAMES_PLAYED',
                             'GP', 'AVG_MINUTES', 'FANTASY_POINTS', 'AVG_FANTASY_PPG']]

df_ranking_output.to_csv('nba_fantasy_rankings_three_metrics.csv', index=False)
print("\nDetailed rankings saved to nba_fantasy_rankings_three_metrics.csv") 