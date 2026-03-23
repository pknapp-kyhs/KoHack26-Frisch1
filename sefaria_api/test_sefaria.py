import requests

# HACKATHON ARCHITECTURE:
# This is a micro-script designed for isolated integration testing.
# Before building the complex database seeding logic, we verify the external Sefaria API 
# data structures independently. This ensures our core data provider is reliable.
ref = "Siddur Ashkenaz, Weekday, Shacharit, Preparatory Prayers, Modeh Ani"

# DATA INGESTION:
# We explicitly request 'text_only' format to strip out unnecessary HTML or markdown 
# from the Sefaria database, reducing payload size and making it easier to parse into our own models.
data = requests.get(
    f"https://www.sefaria.org/api/v3/texts/{ref}",
    params={"return_format": "text_only", "version": "english"}
).json()

print(data)