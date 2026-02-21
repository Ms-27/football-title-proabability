#!/usr/bin/env python3
"""
Script pour extraire les prédictions de titre Ligue 1 depuis Opta Analyst
Utilise Selenium pour cliquer sur l'onglet PREDICTED et extraire les vraies probabilités
"""

import argparse
import re
import time
from typing import Dict, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class Ligue1OptaPredictions:
    """Extracteur de prédictions Ligue 1 depuis Opta Analyst"""
    
    def __init__(self) -> None:
        self.driver: Optional[webdriver.Chrome] = None
        self.title_probabilities: Dict[str, float] = {}
        self._setup_driver()
    
    def _setup_driver(self) -> None:
        """Configure Chrome en mode headless"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Driver Selenium initialisé")
            
        except Exception as e:
            print(f"❌ Erreur initialisation Selenium: {e}")
            self.driver = None
    
    def extract_predictions(self) -> bool:
        """Extrait les vraies prédictions de titre depuis Opta Analyst"""
        if not self.driver:
            return False
        
        print("🔍 Extraction des prédictions de titre...")
        
        # Charger la page table
        print("🌐 Chargement page table...")
        self.driver.get("https://theanalyst.com/competition/ligue-1/table")
        time.sleep(5)
        
        # Cliquer sur l'onglet PREDICTED
        if not self._click_predicted_tab():
            return False
        
        # Extraire les prédictions
        predictions = self._parse_predictions()
        if predictions:
            self.title_probabilities = predictions
            return True
        
        return False
    
    def _click_predicted_tab(self) -> bool:
        """Clique sur l'onglet PREDICTED"""
        print("🔍 Recherche onglet PREDICTED...")
        
        selectors = [
            "//button[contains(text(), 'PREDICTED')]",
            "//button[contains(@class, 'Button-module_button-coin-active')]",
            "//button[@aria-controls*='predicted']",
            "//button[contains(@aria-controls, 'predicted')]"
        ]
        
        for selector in selectors:
            try:
                button = self.driver.find_element(By.XPATH, selector)
                print("✅ Bouton PREDICTED trouvé")
                
                # Cliquer avec JavaScript pour éviter les blocages
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(3)
                return True
                
            except Exception:
                continue
        
        print("❌ Bouton PREDICTED non trouvé")
        return False
    
    def _parse_predictions(self) -> Dict[str, float]:
        """Parse les prédictions depuis l'onglet PREDICTED"""
        try:
            time.sleep(2)
            page_source = self.driver.page_source
            predictions: Dict[str, float] = {}
            
            # Patterns ordonnés pour éviter les doublons
            patterns = [
                (r'Paris SG.*?(\d{2}\.\d{2})%', 'Paris SG'),
                (r'PSG.*?(\d{2}\.\d{2})%', 'Paris SG'),
                (r'Lens.*?(\d{2}\.\d{2})%', 'Lens'),
                (r'Lyon.*?(\d{1}\.\d{2})%', 'Lyon'),
                (r'Marseille.*?(\d{1}\.\d{2})%', 'Marseille')
            ]
            
            for pattern, team in patterns:
                if team not in predictions:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        prob = float(matches[0])
                        predictions[team] = prob
                        print(f"  ✅ {team}: {prob}%")
            
            return predictions
            
        except Exception as e:
            print(f"❌ Erreur parsing: {e}")
            return {}
    
    def print_predictions(self) -> None:
        """Affiche les prédictions dans la console"""
        if not self.title_probabilities:
            print("❌ Aucune prédiction à afficher")
            return
        
        print("\n" + "=" * 80)
        print("  PRÉDICTIONS TITRE LIGUE 1 2025-26")
        print("=" * 80)
        print("  Source: Opta Analyst (onglet PREDICTED)")
        print("=" * 80)
        
        # Trier par probabilité décroissante
        sorted_predictions = sorted(self.title_probabilities.items(), key=lambda x: x[1], reverse=True)
        
        for team, prob in sorted_predictions:
            bar_length = 50
            filled = int(prob / 2)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"  {team:<20} {bar} {prob:6.2f}%")
        
        print("=" * 80)
    
    def close(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            print("🔚 Driver fermé")

def main() -> None:
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Prédictions Ligue 1 depuis Opta Analyst",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python ligue1_opta_prediction.py

Ce script extrait les prédictions de titre depuis l'onglet PREDICTED
d'Opta Analyst et les affiche dans la console.
        """
    )
    
    try:
        print("=" * 60)
        print("PRÉDICTIONS LIGUE 1 - OPTA ANALYST")
        print("=" * 60)
        print("Source: Opta Analyst (onglet PREDICTED)")
        print("=" * 60)
        
        # Initialiser l'extracteur
        extractor = Ligue1OptaPredictions()
        
        if extractor.driver:
            try:
                # Extraire les prédictions
                if extractor.extract_predictions():
                    extractor.print_predictions()
                    print("\n🎉 Prédictions extraites avec succès!")
                else:
                    print("❌ Impossible d'extraire les prédictions")
                    
            finally:
                extractor.close()
        else:
            print("❌ Impossible d'initialiser Selenium")
            
    except KeyboardInterrupt:
        print("\n⚠️ Opération annulée")
        if 'extractor' in locals():
            extractor.close()
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
