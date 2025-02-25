import re

def get_line_nums_of_categories(file_name: str):
    """Gets each food category and the respective line number and 
    returns it as a tuple containing two lists"""
    
    with open(file_name, "r") as file:
        html_string = file.read()
    categories = re.findall(r"--\s*(?!.*\b(Aurora|aspx)\b)(.*?)\s*--", html_string)
    target_strings = []
    line_nums = []
    for tuple in categories:    
        target_strings.append(tuple[1])  
    with open(file_name, 'r') as file:
        for line_number, line in enumerate(file, 1):
            for target_string in target_strings:
                formatted_string = "-- " + target_string + " --"
                if formatted_string in line: 
                    line_nums.append(line_number)
    return dict(zip(line_nums, target_strings))