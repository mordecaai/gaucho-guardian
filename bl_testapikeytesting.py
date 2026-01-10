#import needed modules
import requests
import pandas as pd #not needed in this example
import numpy as np #not needed in this example

# Define the API endpoint and parameters
url = "https://api.example.com/data"
params = {
    "param1": "value1",
    "param2": "value2"
}

#api setup stuff
my_api_key = "e4ZhyOTnd3W3SIo6cF481Vs3NSAQKdAL"

#base url for requesting data from the UCSB API
base_url = "https://api.ucsb.edu/academics/curriculums/v3/classes"

#request_url example = f"https://api.ucsb.edu/academics/curriculums/v3/classes/{quarter}/{enroll_code}?includeClassSections=true"

def get_ucsb_class_info(api_key, quarter, enroll_code):
    """
    Retrieves detailed course information from the UCSB Academic Curriculums API.

    This function handles the construction of the URL, the authentication headers,
    and basic error handling for the HTTP response.
    """

    # Construct the final endpoint URL using an f-string.
    # We append '?includeClassSections=true' to the end of the URL as a query
    # parameter to ensure the JSON includes the nested section and seat data.
    request_url = f"{base_url}/{quarter}/{enroll_code}?includeClassSections=true"

    # Define the dictionary of HTTP headers.
    # 'Accept' tells the server we want the data in JSON format.
    # 'ucsb-api-key' is the custom header required by UCSB for authentication.
    headers = {
        "Accept": "application/json",
        "ucsb-api-key": api_key
    }

    # Execute the GET request to the UCSB servers.
    # We pass both the URL and the headers dictionary.
    response = requests.get(request_url, headers=headers)

    # Check the HTTP status code returned by the server.
    # 200 is the standard 'Success' code.
    if response.status_code == 200:
        # Parse the raw response text into a Python dictionary (JSON).
        class_data = response.json()
        return class_data
    else:
        # If the request fails (e.g., 401 Unauthorized or 404 Not Found),
        # we log the error code to the console for debugging purposes.
        print(f"Failed to retrieve data: Code {response.status_code}")

        # Return None to signal to the rest of the program that no data was found.
        return None
# Example usage of the function

#Execution of getting a ucsb class's name, number of units, grading option

#example input (my api key is defined above)
my_quarter = "20261" #2026 winter quarter
my_enroll_code = "29496" #5 digit: this one is for MATH 4B - DIFF EQUATIONS

#runs the function to get class data
class_data = get_ucsb_class_info(my_api_key, my_quarter, my_enroll_code)

#printing the course's infomation stored in the class_data variable
if class_data:
  #Name of Course
  print(f"Name: {class_data['title']}")

  #Units of Course (may be fixed or variable)
  if class_data.get("unitsFixed", 0) > 0:
    print(f"Units: {class_data['unitsFixed']}")
  elif class_data.get("unitsVariableHigh", 0) > 0:
    low = class_data['unitsVariableLow']
    high = class_data['unitsVariableHigh']
    print(f"Units: {low} - {high} (Variable)")
  else:
    print("Units: 0 (Non-credit or section)")

  #Grading Option of Course
  # If gradingOption is missing or None, it will display "Standard Letter"
  grading = class_data.get('gradingOption') or "Standard Letter"
  print(f"Grading Option: {grading}")

  # Enrollment Status
  # The 'status' field usually returns strings like 'Open', 'Closed', or 'Full'
  current_status = class_data.get('status', 'Unknown')
  print(f"Status: {current_status}")

  # Seat Calculation (enrolledTotal vs maxEnroll)
  # We use .get(key, 0) to ensure we have a number to subtract, avoiding errors
  enrolled = class_data.get('enrolledTotal', 0)
  maximum = class_data.get('maxEnroll', 0)
  seats_left = maximum - enrolled

  print(f"Enrollment: {enrolled}/{maximum} ({seats_left} seats remaining)")
