import requests
import json  # 📦 Import the json module

MY_API_KEY = input("Enter your API key: ")

headers = {
    'accept': 'application/json', # 📄 Updated to request JSON
    'ucsb-api-key': MY_API_KEY
}
date = "20261"
class_code = "38687"
url = f"https://api.ucsb.edu/academics/curriculums/v3/classes/{date}/{class_code}?includeClassSections=true"

def download_class_data(url, headers):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            # 💾 Here is where we save the file
            filename = f"class_{class_code}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4) # 'indent' makes it readable
            
            print(f"✅ Success! Data saved to {filename}")
            return True
        else:
            print("❌ No data found.")
            return False
    else:
        print(f"⚠️ Request failed with status code: {response.status_code}")
        return False

# Test the download
download_class_data(url, headers)