import requests
import re
import json
import datetime
from tqdm import tqdm

class NutritionScraper():
    
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

    #header to be used for scraping
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

    # returns link to main nutrition website
    def getMainLink(self):
        return ( self.mainLink + 
                self.getDiningHallLink(self.locationName) + 
                self.datePrefix + 
                self.monthString + 
                self.dayString + 
                self.yearString + 
                self.meal ) 

    def getDiningHallLink(self, name):
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
    def getCleanHeader(self, inputStr):
        headerList = [[item for item in rowString.split(": ")] for rowString in inputStr.split("\n")]
        headers = {x[0].strip():x[1].strip() for x in headerList}
        return headers
    
    # returns macronutrient in nutrition label
    def findMacronutrient(self, response, nutrientName):
        #gets index of the nutrient
        findIndex = response.find(nutrientName)
        #gets substring containing nutrient info
        nutrientString = response[findIndex:findIndex + 100]
        #gets index of end of nutrient amount
        findIndex2 = nutrientString.find("g")
        #finds index of start of nutrient amount
        i = findIndex2
        while(True):
            if nutrientString[i:i+1] == ">":
                i += 1
                break
            elif nutrientString[i:i+1] == "-":
                return "0"
            i -= 1
            if i == 0:
                break
        returnStr = nutrientString[i:findIndex2]
        #checks if nutrient is in milligrams or grams
        if(returnStr[len(returnStr)-1:] == "m"):
            return returnStr
        return returnStr

    #returns number of calories in nutrition label
    def getCalories(self, response):
        findIndexCalories = response.find("Calories")
        calorieString = response[findIndexCalories:findIndexCalories+100]
        findIndex2 = calorieString.find("p;")
        i = findIndex2 + 2
        while(True):
            if calorieString[i:i+1] == "<":
                break
            i += 1
            if i == 1000:
                break
        return calorieString[findIndex2+2:i]
    
        
    #returns dictionary of macronutrients and the amount of said macronutrient
    def getAllMacros(self, response):
        macroList = ["Total Fat", "Tot. Carb.", "Protein"]
        macros = {}
        macros["Calories"] = float(self.getCalories(response))
        for macro in macroList:
            macros[macro] = float(self.findMacronutrient(response,macro))
        return macros

    def addPrefix(self, string):
        return self.linkPrefix + string 
    def scrapeNutrition(self):
        headers = self.getCleanHeader(self.headerString)
        responseMain = requests.get(self.getMainLink(), headers=headers, verify=False)

        f = open("output.html", "w")
        f.write(responseMain.text)
        print(responseMain.headers)
        f.close()

        f = open("output.html", "r")
        htmlString = f.read()
        # responseMain = requests.get(mainLink, headers=headers)

        # regex pattern to pull links from file
        linkPattern = r"'(label\.aspx\?[^']*)\'"
        # regex pattern to pull food names from file
        namePattern = r"';\">([^<]+)</a>"

        names = list(re.findall(namePattern, htmlString))
        links = list(re.findall(linkPattern, htmlString))
        links = list(map(self.addPrefix, links))
        nutritionList = []
        # loop over each match
        for i in tqdm (range(len(links)), desc="Scraping Nutrition..."):
            response = requests.get(links[i], headers=headers, verify=False)
            nutritionInfo = self.getAllMacros(response.text)
            nutritionList.append(nutritionInfo)
        nutritionDict = {name:info for (name,info) in zip(names,nutritionList)}
            
        dict = {name:link for (name,link) in zip(names,links)}
        if(len(nutritionDict) == 0):
            print("Error")
        else:
            print("Success!")
        f.close()
        # writes results to json file
        with open("nutritionInfo.json", "w") as f:
            json.dump(nutritionDict, f, indent=4)
        f.close()
        
scraper = NutritionScraper()
scraper.scrapeNutrition()