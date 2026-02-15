import argparse
import importlib
import numpy as np
from scipy.stats import poisson
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# Parameters: Current standings and team stats
from config import MATCHES_PLAYED, TEAM_DATA, RATIO_WEIGHT, POISSON_WEIGHT, CLEANSHEET_WEIGHT, SCORING_WEIGHT, FORM_WEIGHT

# Derived lists (indexed by team order)
TEAMS = list(TEAM_DATA.keys())
POINTS = [TEAM_DATA[t]['wins'] * 3 + TEAM_DATA[t]['draws'] for t in TEAMS]
REMAINING_MATCHES = [TEAM_DATA[t]['remaining'] for t in TEAMS]
WIN_RATIO = [TEAM_DATA[t]['wins'] / MATCHES_PLAYED for t in TEAMS]
DRAW_RATIO = [TEAM_DATA[t]['draws'] / MATCHES_PLAYED for t in TEAMS]
AVG_SCORED = [TEAM_DATA[t]['scored'] / MATCHES_PLAYED for t in TEAMS]
AVG_CONCEDED = [TEAM_DATA[t]['conceded'] / MATCHES_PLAYED for t in TEAMS]
CLEAN_SHEET_RATE = [TEAM_DATA[t]['cleansheet_rate'] for t in TEAMS]
SCORING_RATE = [TEAM_DATA[t]['scoring_rate'] for t in TEAMS]
RECENT_FORM = [TEAM_DATA[t]['recent_form'] for t in TEAMS]

# League-wide average (to adjust relative strengths)
LEAGUE_AVG = np.mean([TEAM_DATA[t]['scored'] for t in TEAMS]) / MATCHES_PLAYED


def poisson_probabilities(att_strength, def_weakness, nb_sim=5000):
    """Compute P(win), P(draw), P(loss) via Poisson simulation"""
    lambda_team = max(att_strength * (def_weakness / LEAGUE_AVG), 0.1)
    lambda_opponent = max(LEAGUE_AVG, 0.1)
    
    goals_team = poisson.rvs(lambda_team, size=nb_sim)
    goals_opponent = poisson.rvs(lambda_opponent, size=nb_sim)
    
    p_win = np.mean(goals_team > goals_opponent)
    p_draw = np.mean(goals_team == goals_opponent)
    p_loss = np.mean(goals_team < goals_opponent)
    return p_win, p_draw, p_loss

# Pre-compute combined probabilities (once)
def compute_combined_probabilities():
    """Pre-compute combined W/D/L probabilities for each team"""
    probas = []
    for i in range(len(TEAMS)):
        others = [j for j in range(len(TEAMS)) if j != i]
        avg_def_weakness = np.mean([AVG_CONCEDED[j] for j in others])
        p_win_poisson, p_draw_poisson, _ = poisson_probabilities(AVG_SCORED[i], avg_def_weakness)
        
        # Form adjustment factor (normalize recent form around 2.0 points per match)
        form_adjustment = 1.0 + FORM_WEIGHT * (RECENT_FORM[i] / 2.0 - 1.0)
        
        # Combined win probability with all factors
        p_win = (RATIO_WEIGHT * WIN_RATIO[i] + 
                 POISSON_WEIGHT * p_win_poisson +
                 CLEANSHEET_WEIGHT * (CLEAN_SHEET_RATE[i] * 0.5) +  # Scale down cleansheet impact
                 SCORING_WEIGHT * (SCORING_RATE[i] * 0.8)) * form_adjustment  # Scale down scoring impact
        
        # Draw probability (form affects both teams equally)
        p_draw = (RATIO_WEIGHT * DRAW_RATIO[i] + 
                  POISSON_WEIGHT * p_draw_poisson) * form_adjustment
        
        probas.append((p_win, p_draw))
    return probas

def simulate_batch(args):
    """Simulate a batch of seasons (runs in a separate process)"""
    nb_sims, team_probas, seed = args
    rng = np.random.default_rng(seed)
    count = np.zeros(len(TEAMS))
    
    for _ in range(nb_sims):
        sim_points = list(POINTS)
        
        for i in range(len(TEAMS)):
            p_win, p_draw = team_probas[i]
            rands = rng.random(REMAINING_MATCHES[i])
            for r in rands:
                if r < p_win:
                    sim_points[i] += 3
                elif r < p_win + p_draw:
                    sim_points[i] += 1
        
        max_pts = max(sim_points)
        champions = [i for i, pts in enumerate(sim_points) if pts == max_pts]
        for c in champions:
            count[c] += 1 / len(champions)
    
    return count


def simulate_season(nb_simulations=100000):
    """Simulate multiple end-of-season scenarios in parallel via multiprocessing"""
    team_probas = compute_combined_probabilities()
    
    nb_workers = cpu_count()
    batch_size = min(1000, nb_simulations)
    nb_batches = nb_simulations // batch_size
    remainder = nb_simulations % batch_size
    
    # Distribute simulations into small batches for smooth progress
    batches = []
    for b in range(nb_batches):
        batches.append((batch_size, team_probas, np.random.randint(0, 2**31) + b))
    if remainder > 0:
        batches.append((remainder, team_probas, np.random.randint(0, 2**31) + nb_batches))
    
    # Parallel execution with progress bar
    total_count = np.zeros(len(TEAMS))
    with Pool(nb_workers) as pool:
        for result in tqdm(pool.imap_unordered(simulate_batch, batches), total=len(batches), desc="Simulation", unit="batch"):
            total_count += result
    
    # Final probabilities
    title_probas = {TEAMS[i]: (total_count[i] / nb_simulations) * 100 for i in range(len(TEAMS))}
    return title_probas

def parse_args():
    parser = argparse.ArgumentParser(description="Simulate Ligue 1 title probabilities")
    parser.add_argument('--sims', type=int, default=100000, help="Number of simulations (default: 100000)")
    parser.add_argument('--config', type=str, default=None, help="Config module name to use instead of 'config' (e.g. config_j25)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Reload config if a custom one is specified
    if args.config:
        global MATCHES_PLAYED, TEAM_DATA, RATIO_WEIGHT, POISSON_WEIGHT, CLEANSHEET_WEIGHT, SCORING_WEIGHT, FORM_WEIGHT
        global TEAMS, POINTS, REMAINING_MATCHES, WIN_RATIO, DRAW_RATIO
        global AVG_SCORED, AVG_CONCEDED, CLEAN_SHEET_RATE, SCORING_RATE, RECENT_FORM, LEAGUE_AVG
        cfg = importlib.import_module(args.config)
        MATCHES_PLAYED = cfg.MATCHES_PLAYED
        TEAM_DATA = cfg.TEAM_DATA
        RATIO_WEIGHT = cfg.RATIO_WEIGHT
        POISSON_WEIGHT = cfg.POISSON_WEIGHT
        CLEANSHEET_WEIGHT = cfg.CLEANSHEET_WEIGHT
        SCORING_WEIGHT = cfg.SCORING_WEIGHT
        FORM_WEIGHT = cfg.FORM_WEIGHT
        TEAMS[:] = list(TEAM_DATA.keys())
        POINTS[:] = [TEAM_DATA[t]['wins'] * 3 + TEAM_DATA[t]['draws'] for t in TEAMS]
        REMAINING_MATCHES[:] = [TEAM_DATA[t]['remaining'] for t in TEAMS]
        WIN_RATIO[:] = [TEAM_DATA[t]['wins'] / MATCHES_PLAYED for t in TEAMS]
        DRAW_RATIO[:] = [TEAM_DATA[t]['draws'] / MATCHES_PLAYED for t in TEAMS]
        AVG_SCORED[:] = [TEAM_DATA[t]['scored'] / MATCHES_PLAYED for t in TEAMS]
        AVG_CONCEDED[:] = [TEAM_DATA[t]['conceded'] / MATCHES_PLAYED for t in TEAMS]
        CLEAN_SHEET_RATE[:] = [TEAM_DATA[t]['cleansheet_rate'] for t in TEAMS]
        SCORING_RATE[:] = [TEAM_DATA[t]['scoring_rate'] for t in TEAMS]
        RECENT_FORM[:] = [TEAM_DATA[t]['recent_form'] for t in TEAMS]
        LEAGUE_AVG = np.mean([TEAM_DATA[t]['scored'] for t in TEAMS]) / MATCHES_PLAYED
    
    title_probs = simulate_season(nb_simulations=args.sims)
    print("\n" + "=" * 80)
    print("  TITLE PROBABILITIES - LIGUE 1")
    print("=" * 80)
    for team, prob in sorted(title_probs.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(prob / 2) + "░" * (50 - int(prob / 2))
        print(f"  {team:<5} {bar} {prob:6.2f}%")
    print("=" * 80)


if __name__ == '__main__':
    main()
