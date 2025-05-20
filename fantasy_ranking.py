import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Load the fantasy data
try:
    df = pd.read_csv(r'C:\nba-fantasy\nba_fantasy_stats_new.csv')
except FileNotFoundError:
    print("Error: File 'nba_fantasy_stats_new.csv' not found.")
    exit()

# Filter out players with very few games or minutes (to avoid outliers)
min_games = 20  # Minimum games played to be considered
min_minutes = 10  # Minimum average minutes per game to be considered
df_filtered = df[(df['GP'] >= min_games) & (df['AVG_MINUTES'] >= min_minutes)].copy()

print(f"Total players: {len(df)}")
print(f"Players after filtering (min {min_games} games, {min_minutes} min/game): {len(df_filtered)}")

# Analyze correlation between key metrics and total fantasy points
print("\nCorrelation with total FANTASY_POINTS:")
correlations = {
    'PCT_MINUTES_PLAYED': df_filtered['PCT_MINUTES_PLAYED'].corr(df_filtered['FANTASY_POINTS']),
    'FANTASY_POINTS_PER_MIN': df_filtered['FANTASY_POINTS_PER_MIN'].corr(df_filtered['FANTASY_POINTS']),
    'AVG_FANTASY_PPG': df_filtered['AVG_FANTASY_PPG'].corr(df_filtered['FANTASY_POINTS']),
    'GP': df_filtered['GP'].corr(df_filtered['FANTASY_POINTS']),
    'AVG_MINUTES': df_filtered['AVG_MINUTES'].corr(df_filtered['FANTASY_POINTS'])
}

for metric, corr in sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True):
    print(f"{metric}: {corr:.4f}")

# Develop a combined ranking metric
# Normalize both metrics to a 0-1 scale
df_filtered['NORM_MINUTES_PCT'] = (df_filtered['PCT_MINUTES_PLAYED'] - df_filtered['PCT_MINUTES_PLAYED'].min()) / \
                                 (df_filtered['PCT_MINUTES_PLAYED'].max() - df_filtered['PCT_MINUTES_PLAYED'].min())

df_filtered['NORM_FANTASY_PER_MIN'] = (df_filtered['FANTASY_POINTS_PER_MIN'] - df_filtered['FANTASY_POINTS_PER_MIN'].min()) / \
                                     (df_filtered['FANTASY_POINTS_PER_MIN'].max() - df_filtered['FANTASY_POINTS_PER_MIN'].min())

# Try different weightings to find optimal combination
weights = [(0.3, 0.7), (0.4, 0.6), (0.5, 0.5), (0.6, 0.4), (0.7, 0.3)]
correlations_by_weight = {}

for w_min, w_fpm in weights:
    # Create weighted score
    df_filtered[f'WEIGHTED_SCORE_{w_min}_{w_fpm}'] = (w_min * df_filtered['NORM_MINUTES_PCT'] + 
                                                     w_fpm * df_filtered['NORM_FANTASY_PER_MIN'])
    
    # Check correlation with total fantasy points
    corr = df_filtered[f'WEIGHTED_SCORE_{w_min}_{w_fpm}'].corr(df_filtered['FANTASY_POINTS'])
    correlations_by_weight[(w_min, w_fpm)] = corr
    print(f"Weights ({w_min}, {w_fpm}) - Correlation with FANTASY_POINTS: {corr:.4f}")

# Find best weighting
best_weights = max(correlations_by_weight.items(), key=lambda x: x[1])
w_min_best, w_fpm_best = best_weights[0]
print(f"\nBest weights: {w_min_best} for % minutes played, {w_fpm_best} for fantasy points per minute")
print(f"Correlation: {best_weights[1]:.4f}")

# Create final ranking score using the best weights
df_filtered['FANTASY_RANK_SCORE'] = (w_min_best * df_filtered['NORM_MINUTES_PCT'] + 
                                     w_fpm_best * df_filtered['NORM_FANTASY_PER_MIN'])

# Calculate percentile rank (0-100 scale, higher is better)
df_filtered['FANTASY_RANK_PERCENTILE'] = df_filtered['FANTASY_RANK_SCORE'].rank(pct=True) * 100

# Sort by the ranking score
df_ranked = df_filtered.sort_values('FANTASY_RANK_SCORE', ascending=False)

# Display top players by season
print("\nTop 10 players for 2023-24 season:")
top_2023_24 = df_ranked[df_ranked['SEASON'] == '2023-24'].head(10)
print(top_2023_24[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'AVG_MINUTES', 
                   'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED', 'FANTASY_RANK_SCORE', 
                   'FANTASY_RANK_PERCENTILE', 'FANTASY_POINTS']])

print("\nTop 10 players for 2024-25 season:")
top_2024_25 = df_ranked[df_ranked['SEASON'] == '2024-25'].head(10)
print(top_2024_25[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'AVG_MINUTES', 
                   'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED', 'FANTASY_RANK_SCORE', 
                   'FANTASY_RANK_PERCENTILE', 'FANTASY_POINTS']])

# Save detailed rankings to CSV
df_ranking_output = df_ranked[['SEASON', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 
                             'FANTASY_RANK_SCORE', 'FANTASY_RANK_PERCENTILE',
                             'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED',
                             'GP', 'AVG_MINUTES', 'FANTASY_POINTS', 'AVG_FANTASY_PPG']]

df_ranking_output.to_csv('nba_fantasy_rankings.csv', index=False)
print("\nDetailed rankings saved to nba_fantasy_rankings.csv")

# Visualize relationship between minutes played and fantasy points per minute
plt.figure(figsize=(12, 8))
scatter = plt.scatter(df_filtered['PCT_MINUTES_PLAYED'], 
                     df_filtered['FANTASY_POINTS_PER_MIN'],
                     c=df_filtered['FANTASY_POINTS'], 
                     cmap='viridis', 
                     alpha=0.7,
                     s=100)

# Add a colorbar legend
cbar = plt.colorbar(scatter)
cbar.set_label('Total Fantasy Points', size=12)

# Label the top players
top_players = df_filtered.nlargest(15, 'FANTASY_POINTS')
for _, player in top_players.iterrows():
    plt.annotate(player['PLAYER_NAME'], 
                (player['PCT_MINUTES_PLAYED'], player['FANTASY_POINTS_PER_MIN']),
                fontsize=8, alpha=0.8)

plt.title('Fantasy Value: % Minutes Played vs Fantasy Points per Minute', size=14)
plt.xlabel('% of Minutes Played', size=12)
plt.ylabel('Fantasy Points per Minute', size=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('fantasy_value_plot.png', dpi=300)
print("Visualization saved to fantasy_value_plot.png") 