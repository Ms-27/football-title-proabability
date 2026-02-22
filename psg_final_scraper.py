#!/usr/bin/env python3
"""
Script pour scraper les matchs PSG depuis histoiredupsg.fr
Extrait: saison, compétition, date, adversaire, score, lieu (domicile/extérieur)
Sauvegarde en JSON par saison
"""

import json
import re
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

class PSGFinalScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # Créer le dossier de sortie s'il n'existe pas
        self.output_dir = "psg_matches_data"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_season_from_url(self, url: str) -> str:
        """Extrait la saison depuis l'URL"""
        match = re.search(r'saison-(\d{4}-\d{4})', url)
        return match.group(1) if match else "inconnue"
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse une date et la retourne au format ISO"""
        if not date_str:
            return None
        
        # Pattern pour dates comme "01/08/70"
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', date_str.strip())
        if match:
            day, month, year = match.groups()
            # Convertir l'année 2 chiffres en 4 chiffres
            if len(year) == 2:
                year = f"19{year}" if int(year) >= 70 else f"20{year}"
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_str
    
    def parse_score(self, score_str: str) -> tuple:
        """Parse un score et retourne (score_psg, score_adversaire)"""
        if not score_str:
            return (None, None)
        
        # Pattern pour scores comme "1-3", "2-0", etc.
        match = re.search(r'(\d+)\s*[-:]\s*(\d+)', score_str.strip())
        if match:
            return (int(match.group(1)), int(match.group(2)))
        
        return (None, None)
    
    def determine_venue(self, match_text: str) -> str:
        """Détermine si le match est à domicile ou extérieur"""
        # Si le format est "PSG – Adversaire", c'est à domicile
        if re.search(r'PSG\s*–\s*[A-Z]', match_text):
            return 'Domicile'
        # Si le format est "Adversaire – PSG", c'est à l'extérieur
        elif re.search(r'[A-Z]\s*–\s*PSG', match_text):
            return 'Extérieur'
        
        return 'Inconnu'
    
    def extract_competition(self, match_text: str) -> str:
        """Extrait la compétition du texte du match"""
        if 'match amical' in match_text.lower():
            return 'Amical'
        elif 'division 2' in match_text.lower():
            return 'Championnat Division 2'
        elif 'coupe de france' in match_text.lower():
            return 'Coupe de France'
        elif 'coupe de la ligue' in match_text.lower():
            return 'Coupe de la Ligue'
        
        return 'Autre'
    
    def clean_opponent_name(self, opponent: str) -> str:
        """Nettoie le nom de l'adversaire"""
        if not opponent:
            return "Inconnu"
        
        # Enlever les suffixes communs
        opponent = re.sub(r'\b(F\.C\.|FC|A\.S\.|AS|O\.S\.|OS|U\.S\.|US|S\.M\.|SM|S\.T\.|ST)\b', '', opponent)
        opponent = re.sub(r'\b(L\.B\.|LB|E\.D\.S\.|EDS|A\.A\.J\.|AAJ|L\.B\.C\.|LBC)\b', '', opponent)
        
        # Nettoyer les espaces multiples
        opponent = re.sub(r'\s+', ' ', opponent).strip()
        
        return opponent
    
    def scrape_season_matches(self, url: str) -> List[Dict]:
        """Scrape les matchs d'une saison spécifique"""
        print(f"🔍 Scraping matchs: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            season = self.extract_season_from_url(url)
            
            # Parser avec BeautifulSoup pour extraire les matchs depuis les span
            soup = BeautifulSoup(response.content, 'html.parser')
            
            matches = []
            
            # Trouver tous les spans qui contiennent des matchs
            # Les matchs sont dans des spans avec style="color: #ffffff;"
            match_spans = soup.find_all('span', style=lambda x: x and 'color: #ffffff' in x)
            
            print(f"📊 {len(match_spans)} spans trouvés")
            
            for span in match_spans:
                span_text = span.get_text()
                
                # Vérifier si ce span contient un match (date + score)
                if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}.*?\d+\s*[-:]\s*\d+', span_text):
                    print(f"  🔍 Span trouvé: {span_text[:100]}...")
                    
                    # Parser le match depuis ce span
                    match_data = self.parse_match_from_span(span_text, season, url)
                    if match_data:
                        matches.append(match_data)
                        print(f"    ✅ {match_data['date_brute']} - {match_data['adversaire']} ({match_data['score_complet']})")
            
            print(f"📊 Total: {len(matches)} matchs extraits")
            return matches
            
        except Exception as e:
            print(f"❌ Erreur scraping {url}: {e}")
            return []
    
    def parse_match_from_span(self, span_text: str, season: str, url: str) -> Optional[Dict]:
        """Parse un match depuis un span spécifique"""
        
        # Nettoyer le texte
        text = span_text.strip()
        text = re.sub(r'&#8211;', '–', text)  # Remplacer les entités HTML
        
        # Pattern principal pour matchs amicaux et simples
        # Ex: "08/08/70, match amical, PSG – Fontainebleau : 1-1"
        match_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*([^,]+),\s*([A-Za-z\s\-\.]+)\s*–\s*([A-Za-z\s\-\.]+)\s*:\s*(\d+\s*[-:]\s*\d+)'
        
        match = re.search(match_pattern, text)
        if match:
            date_str, competition, team1, team2, score_str = match.groups()
            return self.create_match_data(date_str, competition, team1, team2, score_str, season, url)
        
        # Pattern pour matchs de championnat avec positions
        # Ex: "23/08/70, Division 2, 1ère journée, Poitiers – PSG : 1-1 (7e)"
        championship_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*([^,]+),\s*([^,]+),\s*([A-Za-z\s\-\.]+)\s*–\s*([A-Za-z\s\-\.]+)\s*:\s*(\d+\s*[-:]\s*\d+)'
        
        match = re.search(championship_pattern, text)
        if match:
            date_str, competition, round_info, team1, team2, score_str = match.groups()
            # Combiner compétition et round_info
            full_competition = f"{competition.strip()}, {round_info.strip()}"
            return self.create_match_data(date_str, full_competition, team1, team2, score_str, season, url)
        
        # Pattern alternatif pour matchs avec format différent
        # Ex: "22/11/70, Coupe de France, 5ème tour, Dieppe – PSG : 0-1"
        cup_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*([^,]+),\s*([^,]+),\s*([A-Za-z\s\-\.]+)\s*–\s*([A-Za-z\s\-\.]+)\s*:\s*(\d+\s*[-:]\s*\d+)'
        
        match = re.search(cup_pattern, text)
        if match:
            date_str, competition, round_info, team1, team2, score_str = match.groups()
            full_competition = f"{competition.strip()}, {round_info.strip()}"
            return self.create_match_data(date_str, full_competition, team1, team2, score_str, season, url)
        
        return None
    
    def create_match_data(self, date_str: str, competition: str, team1: str, team2: str, score_str: str, season: str, url: str) -> Optional[Dict]:
        """Crée un dictionnaire de match depuis les éléments parsés"""
        
        # Déterminer qui est PSG et qui est l'adversaire
        if 'PSG' in team1.upper() or 'PARIS' in team1.upper():
            opponent = team2.strip()
            venue = 'Domicile'
        elif 'PSG' in team2.upper() or 'PARIS' in team2.upper():
            opponent = team1.strip()
            venue = 'Extérieur'
        else:
            return None
        
        # Parser le score
        psg_score, opponent_score = self.parse_score(score_str)
        
        # Si PSG est à l'extérieur, inverser les scores
        if venue == 'Extérieur' and psg_score is not None:
            psg_score, opponent_score = opponent_score, psg_score
        
        # Nettoyer les noms
        opponent = self.clean_opponent_name(opponent)
        competition = competition.strip()
        
        return {
            'saison': season,
            'competition': competition,
            'date': self.parse_date(date_str),
            'date_brute': date_str,
            'adversaire': opponent,
            'score_psg': psg_score,
            'score_adversaire': opponent_score,
            'score_complet': score_str,
            'lieu': venue,
            'url_source': url,
            'date_extraction': datetime.now().isoformat()
        }
    
    def load_urls_from_file(self, filename: str = "seasons_to_scrape.txt") -> List[str]:
        """Charge les URLs à scraper depuis un fichier texte"""
        urls = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Ignorer les lignes vides et les commentaires
                    if line and not line.startswith('#'):
                        urls.append(line)
            
            print(f"📋 {len(urls)} URLs trouvées dans {filename}")
            return urls
            
        except FileNotFoundError:
            print(f"❌ Fichier {filename} non trouvé")
            return []
        except Exception as e:
            print(f"❌ Erreur lecture {filename}: {e}")
            return []
    
    def get_data_hash(self, data: List[Dict]) -> str:
        """Génère un hash des données pour détecter les changements"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    def load_existing_data(self, filename: str) -> tuple[List[Dict], str]:
        """Charge les données existantes et retourne (données, hash)"""
        if not os.path.exists(filename):
            return [], ""
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data_hash = self.get_data_hash(data)
            return data, data_hash
            
        except Exception as e:
            print(f"⚠️ Erreur chargement {filename}: {e}")
            return [], ""
    
    def save_to_json(self, matches: List[Dict], season: str) -> None:
        """Sauvegarde les matchs en JSON par saison dans le dossier dédié"""
        filename = os.path.join(self.output_dir, f"psg_matches_{season.replace('-', '_')}.json")
        
        try:
            # Charger les données existantes
            existing_data, existing_hash = self.load_existing_data(filename)
            
            # Calculer le hash des nouvelles données
            new_hash = self.get_data_hash(matches)
            
            # Vérifier si les données ont changé
            if existing_data and existing_hash == new_hash:
                print(f"🔄 Aucun changement détecté pour {season}, fichier non mis à jour")
                return
            
            # Sauvegarder les nouvelles données
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(matches, f, indent=2, ensure_ascii=False)
            
            if existing_data:
                print(f"� Données mises à jour: {filename} ({len(matches)} matchs)")
            else:
                print(f"� Nouveau fichier créé: {filename} ({len(matches)} matchs)")
                
        except Exception as e:
            print(f"❌ Erreur sauvegarde JSON: {e}")
    
    def get_statistics(self, matches: List[Dict]) -> Dict:
        """Retourne des statistiques sur les matchs"""
        if not matches:
            return {}
        
        total_matches = len(matches)
        
        # Stats par lieu
        venues = {'Domicile': 0, 'Extérieur': 0, 'Inconnu': 0}
        wins = draws = losses = 0
        
        # Stats par compétition
        competitions = {}
        
        for match in matches:
            venue = match['lieu']
            if venue in venues:
                venues[venue] += 1
            
            comp = match['competition']
            if comp not in competitions:
                competitions[comp] = 0
            competitions[comp] += 1
            
            # Stats de résultats
            if match['score_psg'] is not None and match['score_adversaire'] is not None:
                if match['score_psg'] > match['score_adversaire']:
                    wins += 1
                elif match['score_psg'] == match['score_adversaire']:
                    draws += 1
                else:
                    losses += 1
        
        return {
            'total_matchs': total_matches,
            'venues': venues,
            'results': {'victoires': wins, 'nuls': draws, 'defaites': losses},
            'competitions': competitions,
            'premier_match': min([m['date'] for m in matches if m['date']]),
            'dernier_match': max([m['date'] for m in matches if m['date']])
        }

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🏆 SCRAPER FINAL MATCHS PSG")
    print("=" * 60)
    
    # Initialiser le scraper
    scraper = PSGFinalScraper()
    
    # Charger les URLs depuis le fichier
    season_urls = scraper.load_urls_from_file()
    
    if not season_urls:
        print("❌ Aucune URL à scraper. Vérifiez le fichier 'seasons_to_scrape.txt'")
        return
    
    try:
        for url in season_urls:
            season = scraper.extract_season_from_url(url)
            print(f"\n{'='*40}")
            print(f"Saison: {season}")
            print(f"{'='*40}")
            
            # Scraper les matchs de la saison
            matches = scraper.scrape_season_matches(url)
            
            if matches:
                # Sauvegarder en JSON par saison (avec gestion de mise à jour)
                scraper.save_to_json(matches, season)
                
                # Afficher les statistiques
                stats = scraper.get_statistics(matches)
                print(f"\n📊 STATISTIQUES SAISON {season}:")
                print(f"Total matchs: {stats.get('total_matchs', 0)}")
                print(f"Victoires: {stats['results']['victoires']}")
                print(f"Nuls: {stats['results']['nuls']}")
                print(f"Défaites: {stats['results']['defaites']}")
                print(f"Domicile: {stats['venues']['Domicile']}")
                print(f"Extérieur: {stats['venues']['Extérieur']}")
                
                print(f"\n🏆 COMPÉTITIONS:")
                for comp, count in stats.get('competitions', {}).items():
                    print(f"  {comp}: {count} matchs")
                
                print(f"\n✅ Saison {season} terminée!")
            else:
                print(f"❌ Aucun match trouvé pour la saison")
        
        print(f"\n🎉 Extraction terminée!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Opération annulée")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
