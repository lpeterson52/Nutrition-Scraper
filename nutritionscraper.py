"""
    This module contains the class NutritionScraper which is used to scrape nutritional from 
    the UCSC website
"""
import re
import datetime
import json
import requests
import urllib3
from tqdm import tqdm

class NutritionScraper():
    """This class """
    def __init__(self):
        urllib3.disable_warnings()
    date = datetime.datetime.now()
    linkPrefix = "https://nutrition.sa.ucsc.edu/"
    mainLink = "https://nutrition.sa.ucsc.edu/longmenu.aspx?sName=UC+Santa+Cruz+Dining&locationNum=40&locationName="
    locationName = "John R. Lewis Dining Hall & College Nine Dining Hall"
    datePrefix = "&naFlag=1&WeeksMenus=UCSC+-+This+Week%27s+Menus&dtdate="
    # dates
    monthString = str(date.month) + "%2f" # gets current month
    dayString = str(date.day) + "%2f" # gets current day
    yearString = str(date.year) + "&mealName=" # gets current year
    mealsByLocation = {"John R. Lewis Dining Hall & College Nine Dining Hall": {"Breakfast", "Lunch", "Dinner", "Late+Night"},
        "Cowell & Stevenson Dining Hall": {"Breakfast", "Lunch", "Dinner", "Late+Night"},
        "Crown & Merrill Dining Hall and Banana Joe's": {"Breakfast", "Lunch", "Dinner", "Late+Night"},
        "Porter & Kresge Dining Hall": {"Breakfast", "Lunch", "Dinner"},
        "Rachel Carson & Oakes Dining Hall": {"Breakfast", "Lunch", "Dinner", "Late+Night"},
        "Oakes Cafe": {"Breakfast", "All+Day"},
        "Global Village Cafe": {"Menu"},
        "Owl's Nest Cafe": {"Breakfast", 'All'},
        "Slug Stop": {"Menu"},
        "UCen Bistro": {"Menu"},
        "Stevenson Coffee House": {"Menu"}}

    # Meal Names:
    # - Breakfast
    # - Lunch
    # - Dinner
    # - Late+Night
    # - All+Day (only for Oakes cafe)
    # - Menu (global village)
    meal = "Lunch"

    # header to be used for scraping
    headerString = """
    accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
    accept-encoding: gzip, deflate, br, zstd
    accept-language: en-US,en;q=0.9
    cache-control: max-age=0
    cookie: nmstat=dbc72b5e-467d-1d4c-4ec0-09407dd3af4e; _hjSessionUser_3860872=eyJpZCI6Ijc1MzFhMmI3LWZmNDUtNWQyOC05MmRjLWNmMGFmNDE3ZWNkNSIsImNyZWF0ZWQiOjE3MjA0Njk0NjAyODIsImV4aXN0aW5nIjp0cnVlfQ==; _ga=GA1.1.1876244345.1720334281; _ga_YSK09XHBWK=GS1.1.1727391092.1.0.1727391095.0.0.0; _ga_BWJ4Z4Y66X=GS1.1.1727406832.10.1.1727407016.0.0.0; _hp2_props.3001039959=%7B%22Base.appName%22%3A%22Canvas%22%7D; _hp2_id.3001039959=%7B%22userId%22%3A%225450010249110384%22%2C%22pageviewId%22%3A%225820543749153110%22%2C%22sessionId%22%3A%223224987423913875%22%2C%22identity%22%3A%22uu-2-3f7fe8885f071a3adb15c8d16cf7c5256e74604a83fdfeb8359e06ffd3bc86be-subopMsfCdn2dwy8anU0QwbgC2CqHbZFnJmMvElg%22%2C%22trackerVersion%22%3A%224.0%22%2C%22identityField%22%3Anull%2C%22isIdentified%22%3A1%7D; PS_DEVICEFEATURES=width:1512 height:982 pixelratio:2 touch:0 geolocation:1 websockets:1 webworkers:1 datepicker:1 dtpicker:1 timepicker:1 dnd:1 sessionstorage:1 localstorage:1 history:1 canvas:1 svg:1 postmessage:1 hc:0 maf:0; WebInaCartDates=; WebInaCartMeals=; WebInaCartRecipes=; WebInaCartQtys=; WebInaCartLocation=40
    priority: u=0, i
    referer: https://nutrition.sa.ucsc.edu/shortmenu.aspx?sName=UC+Santa+Cruz+Dining&locationNum=40&locationName=John+R.+Lewis+%26+College+Nine+Dining+Hall&naFlag=1
    sec-ch-ua: "Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"
    sec-ch-ua-mobile: ?0
    sec-ch-ua-platform: "macOS"
    sec-fetch-dest: document
    sec-fetch-mode: navigate
    sec-fetch-site: same-origin
    sec-fetch-user: ?1
    upgrade-insecure-requests: 1
    user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36
    """.strip()

    def get_main_link(self):
        """Returns link to main nutrition website"""
        return ( self.mainLink +
                self.get_dining_hall_link(self.locationName) +
                self.datePrefix +
                self.monthString +
                self.dayString +
                self.yearString +
                self.meal )

    def get_dining_hall_link(self, name):
        """Converts Dining Hall name into URL form"""
        s = ""
        words = name.split()
        for word in words:
            match word:
                case "&":
                    s += "%26"
                case _:
                    s += word
            s += "+"
        return s[:len(s)-1]

    # puts headerString into key value pairs
    def get_clean_header(self, input_str):
        """Converts headerString into a dictionary"""
        header_list = [list(rowString.split(": ")) for rowString in input_str.split("\n")]
        headers = {x[0].strip():x[1].strip() for x in header_list}
        return headers

    # returns macronutrient in nutrition label
    def find_macronutrient(self, response, nutrient_name):
        """Returns the amount of a specified nutrient
        
        Args:
            response: The text from the scraped nutrition label.
            nutrient_name: The name of the nutrient which will be found.
        
        Returns:
            A string containing the amount of the given macronutrient.
        """
        #gets index of the nutrient
        find_index = response.find(nutrient_name)
        #gets substring containing nutrient info
        nutrient_string = response[find_index:find_index + 100]
        #gets index of end of nutrient amount
        find_index_2 = nutrient_string.find("g")
        #finds index of start of nutrient amount
        i = find_index_2
        while True:
            if nutrient_string[i:i+1] == ">":
                i += 1
                break
            if nutrient_string[i:i+1] == "-":
                return "0"
            i -= 1
            if i == 0:
                break
        return_str = nutrient_string[i:find_index_2]
        #checks if nutrient is in milligrams or grams
        if return_str[len(return_str)-1:] == "m":
            return return_str
        return return_str

    #r eturns number of calories in nutrition label
    def get_calories(self, response):
        """Returns a string with the amount of calories on the given nutrition label
        
        Args:
            response: The text from the scraped nutrition label.
        Returns:
            A string containing the amount of calories on the given nutrition label
        """
        find_index_calories = response.find("Calories")
        calorie_string = response[find_index_calories:find_index_calories+100]
        find_index_2 = calorie_string.find("p;")
        i = find_index_2 + 2
        while True:
            if calorie_string[i:i+1] == "<":
                break
            i += 1
            if i == 1000:
                break
        return calorie_string[find_index_2+2:i]


    # returns dictionary of macronutrients and the amount of said macronutrient
    def get_all_macros(self, response):
        """Returns dictionary containing the macronutrients of a given nutrition label"""
        macro_list = ["Total Fat", "Tot. Carb.", "Protein"]
        macros = {}
        macros["Calories"] = float(self.get_calories(response))
        for macro in macro_list:
            macros[macro] = float(self.find_macronutrient(response,macro))
        return macros

    def add_prefix(self, string):
        """Returns a string with the link prefix prepended to the given string"""
        return self.linkPrefix + string
    def scrape_nutrition(self):
        """Scrapes the nutritional info of a given time period from a given UCSC dining hall 
        and dumps the result into a JSON
        """
        headers = self.get_clean_header(self.headerString)
        response_main = requests.get(self.get_main_link(), headers=headers, verify=False, timeout=2)
        with open("output.html", "w", encoding="utf-8") as f:
            f.write(response_main.text)
            print(response_main.headers)
        with open("output.html", "r", encoding="utf-8") as f:
            html_string = f.read()
        # regex pattern to pull links from file
        link_pattern = r"'(label\.aspx\?[^']*)\'"
        # regex pattern to pull food names from file
        name_pattern = r"';\">([^<]+)</a>"
        names = list(re.findall(name_pattern, html_string))
        links = list(re.findall(link_pattern, html_string))
        links = list(map(self.add_prefix, links))
        nutrition_list = []
        # loop over each match
        for i in tqdm (range(len(links)), desc="Scraping Nutrition..."):
            response = requests.get(links[i], headers=headers, verify=False, timeout=2)
            nutrition_info = self.get_all_macros(response.text)
            nutrition_list.append(nutrition_info)
        nutrition_dict = dict(zip(names,nutrition_list))
        if len(nutrition_dict) == 0:
            print("Error, dictionary empty")
        else:
            print("Success!")
        # writes results to json file
        with open("nutritionInfo.json", "w", encoding="utf-8") as f:
            json.dump(nutrition_dict, f, indent=4)
