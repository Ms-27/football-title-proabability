# Weighting example: 40% historical ratios, 20% Poisson model, 15% cleansheet, 15% scoring, 10% recent form
RATIO_WEIGHT = 0.4
POISSON_WEIGHT = 0.2
CLEANSHEET_WEIGHT = 0.15
SCORING_WEIGHT = 0.15
FORM_WEIGHT = 0.1

# Matches data
MATCHES_PLAYED = 21

TEAM_DATA = {
    'TEAM_NAME': {
        'scored': 0,           # Total goals scored
        'conceded': 0,         # Total goals conceded  
        'remaining': 0,        # Matches remaining to play
        'wins': 0,             # Total wins
        'draws': 0,            # Total draws
        'cleansheet_rate': 0.0,  # % of matches without conceding goals (0.0-1.0, will be scaled by 0.5)
        'scoring_rate': 0.0,     # % of matches scoring at least 1 goal (0.0-1.0, will be scaled by 0.8)
        'recent_form': 0.0       # Average points per match over last 8 games
        # Note: points will be calculated automatically (3 * wins + 1 * draws)
    },
    # Add more teams here...
}

# Example with real data:
# TEAM_DATA = {
#     'PSG': {'scored': 48, 'conceded': 16, 'remaining': 12, 'wins': 17, 'draws': 3, 
#             'cleansheet_rate': 0.5, 'scoring_rate': 0.91, 'recent_form': 2.63},
#     'RCL': {'scored': 37, 'conceded': 17, 'remaining': 12, 'wins': 16, 'draws': 1,
#             'cleansheet_rate': 0.41, 'scoring_rate': 0.82, 'recent_form': 2.63},
# }
