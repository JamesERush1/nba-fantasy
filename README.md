# NBA Fantasy Basketball Analysis Tools

A collection of Python tools for analyzing and optimizing NBA fantasy basketball teams.

## Overview

This project provides tools to:
1. Fetch NBA player statistics from official sources
2. Calculate fantasy points based on standard scoring systems
3. Rank players using a sophisticated three-metric approach
4. Recommend available players for pickup

## Key Components

### Data Collection
- `nba_api.py`: Fetches player statistics from NBA.com and calculates fantasy points

### Player Analysis
- `fantasy_ranking.py`: Analyzes player data and generates rankings using three key metrics:
  - **% Minutes Played**: How much of all possible minutes a player plays
  - **Fantasy Points Per Minute**: How efficient a player is when on the court
  - **% Games Played**: How reliable a player is in terms of availability

### Pickup Recommendations
- `recommend_pickups.py`: Matches available players against rankings to recommend the best pickups

## The Three-Metric Ranking System

Our ranking system balances three critical factors for fantasy basketball success:

1. **% Minutes Played** - Measures how much a player is utilized by their team
2. **Fantasy Points Per Minute** - Measures efficiency when on the court
3. **% Games Played** - Measures reliability/durability

The system analyzes different weight combinations for these metrics and determines the optimal weights that correlate best with total fantasy production. This balanced approach provides a more accurate picture of a player's true fantasy value than traditional metrics.

## Usage

1. **Fetch Data**:
   ```
   python nba_api.py
   ```

2. **Generate Rankings**:
   ```
   python fantasy_ranking.py
   ```

3. **Get Pickup Recommendations**:
   ```
   python recommend_pickups.py --file your_available_players.csv
   ```
   Or run without arguments for interactive mode:
   ```
   python recommend_pickups.py
   ```

## Sample Files

- `available_players_sample.csv`: A sample file showing the format for available players

## Requirements

- Python 3.6+
- pandas
- numpy
- scipy
- requests

## Scripts

### 1. Fantasy Ranking Script (`fantasy_ranking.py`)

Analyzes NBA player stats and generates advanced fantasy rankings based on reliability and usage rate.

**Features:**
- Aggregates player data across seasons
- Calculates reliability scores based on games played
- Estimates usage rates to measure player involvement
- Generates optimal weightings between metrics
- Ranks players based on combined metrics

**Output:**
- `nba_fantasy_rankings_new_metrics.csv`: Complete player rankings
- `new_metrics_analysis.txt`: Analysis of metric importance

### 2. ESPN Fantasy Scraper (`fantasy_espn_scraper.py`)

Scrapes available players from your ESPN fantasy basketball league and recommends pickups based on our rankings.

**Features:**
- Automatically scrapes available players from ESPN fantasy basketball
- Matches players with our custom rankings
- Recommends the best available players to add
- Saves detailed pickup recommendations

**Output:**
- `fantasy_pickup_recommendations.csv`: Ranked list of recommended pickups
- `unmatched_available_players.csv`: List of players not found in our rankings

## Ranking Methods

This repository offers two different ranking approaches:

### Original Method: Minutes Played & Fantasy Points per Minute

The original ranking method (`fantasy_ranking.py` default) focuses on two key metrics:
- **% of Minutes Played**: How much of the available playing time a player gets
- **Fantasy Points per Minute**: How productive a player is when on the court

This method tends to favor star players who get heavy minutes and produce efficiently.

**Outputs**:
- `nba_fantasy_rankings_original.csv`: Rankings using the original method
- `original_weight_analysis.txt`: Analysis of the optimal weights (currently 50/50)
- `fantasy_value_plot_original.png`: Visualization of the player distribution 

### Alternative Method: Reliability & Usage Rate

For an alternative approach, an experimental method using reliability and usage rate is available by uncommenting those sections in the code.
- **Reliability Score**: Measures a player's availability and consistency
- **Usage Rate**: Estimates a player's involvement in the offense when on the court

This method may better identify consistent, season-long performers who are less likely to have extreme ups and downs.

## Which Method Should You Use?

- **Original Method**: Better for identifying the top overall fantasy producers based on traditional metrics
- **Alternative Method**: Better for finding reliable, consistent performers who might be undervalued

Choose the method that best aligns with your fantasy league's scoring system and your team-building strategy.

## Requirements

```
pandas
numpy
scipy
selenium
webdriver_manager
```

## Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install pandas numpy scipy selenium webdriver_manager
   ```
3. Make sure you have Chrome installed (required for the ESPN scraper)

## Usage

### Step 1: Generate Player Rankings

Run the ranking script to analyze player data and generate rankings:

```
python fantasy_ranking.py
```

This will create the ranking files needed for the next step.

### Step 2: Get Pickup Recommendations

Run the ESPN scraper to get personalized pickup recommendations:

```
python fantasy_espn_scraper.py
```

The script will prompt you for:
- ESPN username
- ESPN password
- League ID (defaults to 1609818238)

## Notes

- The login functionality in the ESPN scraper is commented out by default for testing. Uncomment it when you're ready to use with your real credentials.
- Player name matching uses normalization to handle variations in how names appear, but some manual matching may be needed.
- Reliability and usage metrics are designed to identify consistent season-long performers rather than just focusing on single-game performances.
- For the most accurate recommendations, run both scripts regularly as player values change throughout the season.

## Customization

You can customize the ranking weights in `fantasy_ranking.py` based on your league's specific scoring system and preferences. 