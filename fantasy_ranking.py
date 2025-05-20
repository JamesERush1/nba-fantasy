import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
                'PCT_MINUTES_PLAYED': np.average(data['PCT_MINUTES_PLAYED'], weights=data['GP'])
            }
            aggregated_data.append(player_data)

# Create new dataframe with aggregated stats
df_filtered = pd.DataFrame(aggregated_data)

print(f"Total players in original data: {len(df)}")
print(f"Players after aggregating and filtering: {len(df_filtered)}")

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
weights = [(0.0, 1.0), (0.1, 0.9), (0.2, 0.8), (0.3, 0.7), (0.4, 0.6), (0.5, 0.5), 
           (0.6, 0.4), (0.7, 0.3), (0.8, 0.2), (0.9, 0.1), (1.0, 0.0)]
correlations_by_weight = {}

print("\nTesting different weight combinations:")
print("---------------------------------------")
print("Weight for % Minutes | Weight for Points/Min | Correlation")
print("---------------------------------------")

for w_min, w_fpm in weights:
    # Create weighted score
    df_filtered[f'WEIGHTED_SCORE_{w_min}_{w_fpm}'] = (w_min * df_filtered['NORM_MINUTES_PCT'] + 
                                                     w_fpm * df_filtered['NORM_FANTASY_PER_MIN'])
    
    # Check correlation with total fantasy points
    corr = df_filtered[f'WEIGHTED_SCORE_{w_min}_{w_fpm}'].corr(df_filtered['FANTASY_POINTS'])
    correlations_by_weight[(w_min, w_fpm)] = corr
    print(f"      {w_min:.1f}         |        {w_fpm:.1f}         |   {corr:.4f}")

# Find best weighting
best_weights = max(correlations_by_weight.items(), key=lambda x: x[1])
w_min_best, w_fpm_best = best_weights[0]
print("\n---------------------------------------")
print(f"Best weights: {w_min_best:.1f} for % minutes played, {w_fpm_best:.1f} for fantasy points per minute")
print(f"Best correlation: {best_weights[1]:.4f}")

# Analyze which factor is more important
minutes_only_corr = correlations_by_weight[(1.0, 0.0)]
points_only_corr = correlations_by_weight[(0.0, 1.0)]
print("\nFactor importance analysis:")
print(f"Correlation using only % minutes played: {minutes_only_corr:.4f}")
print(f"Correlation using only fantasy points per minute: {points_only_corr:.4f}")

if minutes_only_corr > points_only_corr:
    relative_importance = minutes_only_corr/points_only_corr
    print(f"% Minutes played is {relative_importance:.2f}x more important than points per minute")
else:
    relative_importance = points_only_corr/minutes_only_corr
    print(f"Fantasy points per minute is {relative_importance:.2f}x more important than % minutes played")

# Create final ranking score using the best weights
df_filtered['FANTASY_RANK_SCORE'] = (w_min_best * df_filtered['NORM_MINUTES_PCT'] + 
                                     w_fpm_best * df_filtered['NORM_FANTASY_PER_MIN'])

# Calculate percentile rank (0-100 scale, higher is better)
df_filtered['FANTASY_RANK_PERCENTILE'] = df_filtered['FANTASY_RANK_SCORE'].rank(pct=True) * 100

# Sort by the ranking score
df_ranked = df_filtered.sort_values('FANTASY_RANK_SCORE', ascending=False)

# Display top players (now aggregated across seasons)
print("\nTop 15 players (aggregated across seasons):")
top_players = df_ranked.head(15)
print(top_players[['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'AVG_MINUTES', 
                  'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED', 'FANTASY_RANK_SCORE', 
                  'FANTASY_RANK_PERCENTILE', 'FANTASY_POINTS']])

# Save detailed rankings to CSV
df_ranking_output = df_ranked[['PLAYER_NAME', 'TEAM_ABBREVIATION', 
                             'FANTASY_RANK_SCORE', 'FANTASY_RANK_PERCENTILE',
                             'FANTASY_POINTS_PER_MIN', 'PCT_MINUTES_PLAYED',
                             'GP', 'AVG_MINUTES', 'FANTASY_POINTS', 'AVG_FANTASY_PPG']]

df_ranking_output.to_csv('nba_fantasy_rankings_aggregated.csv', index=False)
print("\nDetailed rankings saved to nba_fantasy_rankings_aggregated.csv")

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

plt.title('Fantasy Value: % Minutes Played vs Fantasy Points per Minute (Aggregated)', size=14)
plt.xlabel('% of Minutes Played', size=12)
plt.ylabel('Fantasy Points per Minute', size=12)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('fantasy_value_plot_aggregated.png', dpi=300)
print("Visualization saved to fantasy_value_plot_aggregated.png") 