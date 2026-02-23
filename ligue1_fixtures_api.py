#!/usr/bin/env python3
"""
Script pour extraire les matchs restants d'une équipe Ligue 1 avec football-data.org
Retourne: adversaire et lieu (domicile/extérieur)
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import argparse

class Ligue1FixturesAPI:
    def __init__(self):
        """Initialise l'extracteur avec l'API football-data.org"""
        self.api_key = "VOTRE_CLÉ_API_ICI"  # Remplacez par votre vraie clé API
        self.base_url = "https://api.football-data.org/v4"
        self.ligue1_id = 61  # ID de la Ligue 1 dans football-data.org
        
        # Mapping des noms d'équipes
        self.team_mapping = {
            'Paris SG': 85,
            'Lyon': 527,
            'Marseille': 532,
            'Monaco': 603,
            'Lille': 521,
            'Lens': 520,
            'Nice': 543,
            'Rennes': 553,
            'Bordeaux': 506,
            'Saint-Étienne': 554,
            'Toulouse': 567,
            'Montpellier': 535,
            'Strasbourg': 562,
            'Nantes': 541,
            'Lorient': 529,
            'Clermont': 511,
            'Reims': 551,
            'Angers': 504,
            'Brest': 508,
            'Metz': 538,
            'Auxerre': 503
        }
    
    def get_team_id(self, team_name: str) -> Optional[int]:
        """Obtient l'ID de l'équipe depuis le mapping"""
        # Chercher une correspondance exacte
        if team_name in self.team_mapping:
            return self.team_mapping[team_name]
        
        # Chercher une correspondance partielle
        for name, team_id in self.team_mapping.items():
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                return team_id
        
        return None
    
    def get_team_fixtures(self, team_name: str) -> Optional[List[Dict[str, str]]]:
        """
        Extrait les matchs restants pour une équipe spécifique
        
        Args:
            team_name: Nom de l'équipe (ex: "Paris SG", "Lyon", "Marseille")
            
        Returns:
            Liste des matchs restants avec adversaire et lieu
        """
        if self.api_key == "VOTRE_CLÉ_API_ICI":
            print("❌ Clé API non configurée")
            print("📝 Veuillez modifier la variable api_key dans la classe Ligue1FixturesAPI")
            print("🔑 Obtenez votre clé gratuite sur: https://www.football-data.org/")
            return None
        
        try:
            team_id = self.get_team_id(team_name)
            if not team_id:
                print(f"❌ Équipe '{team_name}' non trouvée")
                print(f"📋 Équipes disponibles: {list(self.team_mapping.keys())}")
                return None
            
            print(f"🔍 Recherche des matchs pour: {team_name} (ID: {team_id})")
            
            # Obtenir la saison en cours
            current_year = datetime.now().year
            if datetime.now().month >= 8:
                season = f"{current_year}"
            else:
                season = f"{current_year-1}"
            
            # Pour la saison 2025-26, utiliser 2025
            season = "2025"
            
            # URL pour les matchs de l'équipe
            url = f"{self.base_url}/teams/{team_id}/matches"
            params = {
                'league': self.ligue1_id,
                'season': season,
                'status': 'SCHEDULED'  # Uniquement les matchs à venir
            }
            
            headers = {'X-Auth-Token': self.api_key}
            
            print(f"🌐 Requête API: {url}")
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if 'matches' not in data:
                print("❌ Aucun match trouvé dans la réponse API")
                return None
            
            matches = data['matches']
            print(f"📊 {len(matches)} matchs programmés trouvés")
            
            # Parser les matchs
            upcoming_matches = []
            
            for match in matches:
                try:
                    match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
                    
                    # Déterminer l'adversaire et le lieu
                    if match['homeTeam']['id'] == team_id:
                        opponent = match['awayTeam']['name']
                        venue = "home"
                    else:
                        opponent = match['homeTeam']['name']
                        venue = "away"
                    
                    upcoming_matches.append({
                        'opponent': opponent,
                        'venue': venue,
                        'date': match_date.strftime('%Y-%m-%d'),
                        'time': match_date.strftime('%H:%M'),
                        'match_info': f"{match['homeTeam']['name']} vs {match['awayTeam']['name']}",
                        'matchday': match.get('matchday', 'N/A')
                    })
                    
                except Exception as e:
                    print(f"⚠️ Erreur parsing match: {e}")
                    continue
            
            # Trier par date chronologique
            upcoming_matches.sort(key=lambda x: x['date'])
            
            print(f"✅ {len(upcoming_matches)} matchs restants trouvés")
            return upcoming_matches
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur API: {e}")
            return None
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction: {e}")
            return None
    
    def print_fixtures_summary(self, fixtures: List[Dict[str, str]], team_name: str):
        """Affiche un résumé des matchs restants"""
        if not fixtures:
            print(f"❌ Aucun match restant pour {team_name}")
            return
        
        print(f"\n⚽ MATCHS RESTANTS - {team_name.upper()}")
        print("=" * 50)
        print(f"📊 Nombre de matchs restants: {len(fixtures)}")
        
        home_count = sum(1 for f in fixtures if f['venue'] == 'home')
        away_count = len(fixtures) - home_count
        
        print(f"🏠 Matchs à domicile: {home_count}")
        print(f"✈️ Matchs à l'extérieur: {away_count}")
        
        print("\n📋 Détails des matchs:")
        for i, fixture in enumerate(fixtures, 1):
            venue_symbol = "🏠" if fixture['venue'] == 'home' else "✈️"
            print(f"  {i}. {fixture['opponent']} ({venue_symbol} {fixture['venue']})")
    
    def print_detailed_fixtures(self, fixtures: List[Dict[str, str]], team_name: str):
        """Affiche les détails complets des matchs"""
        if not fixtures:
            return
        
        print(f"\n📅 DÉTAILS COMPLETS - {team_name.upper()}")
        print("=" * 60)
        
        for i, fixture in enumerate(fixtures, 1):
            venue_symbol = "🏠" if fixture['venue'] == 'home' else "✈️"
            venue_text = "Domicile" if fixture['venue'] == 'home' else "Extérieur"
            
            print(f"\n{i}. {fixture['opponent']}")
            print(f"   📅 Date: {fixture['date']}")
            print(f"   ⏰ Heure: {fixture['time']}")
            print(f"   📍 Lieu: {venue_text} {venue_symbol}")
            print(f"   🏟️  Journée: {fixture['matchday']}")
            print(f"   📋 Match: {fixture['match_info']}")
    
    def save_to_json(self, fixtures: List[Dict[str, str]], team_name: str, filename: str = None):
        """Sauvegarde les fixtures en format JSON"""
        if not filename:
            filename = f"fixtures_{team_name.lower().replace(' ', '_')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(fixtures, f, indent=2, ensure_ascii=False)
            print(f"💾 Données sauvegardées dans: {filename}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Extraction des matchs restants Ligue 1 avec football-data.org",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python ligue1_fixtures_api.py "Paris SG"
  python ligue1_fixtures_api.py "Lyon" --save --detailed
  python ligue1_fixtures_api.py "Marseille" --output mes_fixtures.json

Configuration requise:
  1. Créez un compte sur https://www.football-data.org/
  2. Obtenez votre clé API gratuite
  3. Configurez la variable api_key dans la classe Ligue1FixturesAPI

Équipes supportées:
  Paris SG, Lyon, Marseille, Monaco, Lille, Lens, Nice, Rennes, 
  Bordeaux, Saint-Étienne, Toulouse, Montpellier, Strasbourg, Nantes,
  Lorient, Clermont, Reims, Angers, Brest, Metz, Auxerre
        """
    )
    
    parser.add_argument('team', help='Nom de l\'équipe (ex: "Paris SG", "Lyon")')
    parser.add_argument('--save', action='store_true', help='Sauvegarder en JSON')
    parser.add_argument('--output', help='Nom du fichier de sortie (optionnel)')
    parser.add_argument('--detailed', action='store_true', help='Afficher les détails complets')
    
    try:
        args = parser.parse_args()
        
        print("="*60)
        print("EXTRACTION MATCHS RESTANTS LIGUE 1 (API)")
        print("="*60)
        print(f"Équipe: {args.team}")
        print(f"Saison: 2025-26")
        print("="*60)
        
        # Initialiser l'extracteur
        extractor = Ligue1FixturesAPI()
        
        # Extraire les fixtures
        fixtures = extractor.get_team_fixtures(args.team)
        
        if fixtures:
            # Afficher le résumé
            extractor.print_fixtures_summary(fixtures, args.team)
            
            # Afficher les détails si demandé
            if args.detailed:
                extractor.print_detailed_fixtures(fixtures, args.team)
            
            # Sauvegarder si demandé
            if args.save:
                extractor.save_to_json(fixtures, args.team, args.output)
            
            print("\n🎉 Opération terminée avec succès!")
        else:
            print("❌ Impossible d'extraire les fixtures")
            
    except KeyboardInterrupt:
        print("\n⚠️ Opération annulée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
