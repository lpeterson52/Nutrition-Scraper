"""Main Method"""

import nutritionscraper
import food

def main():
    """Main method"""
    scraper = nutritionscraper.NutritionScraper()
    scraper.scrape_nutrition()

if __name__ == "__main__":
    main()
