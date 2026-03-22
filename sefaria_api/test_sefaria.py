import requests

ref = "Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani"

data = requests.get(
    f"https://www.sefaria.org/api/v3/texts/{ref}",
    params={"return_format": "text_only", "version": "english"}
).json()

print(data)