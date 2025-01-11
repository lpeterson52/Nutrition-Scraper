"""Main Method"""

import nutritionscraper

def main():
    """Main method"""
    scraper = nutritionscraper.NutritionScraper()
    scraper.scrape_nutrition()

if __name__ == "__main__":
    main()
