import requests
import json

# GBIF API endpoint for species data
TAXON_ID = 12162492
SPECIES_URL = f"https://api.gbif.org/v1/species/{TAXON_ID}"
OCCURRENCE_URL = f"https://api.gbif.org/v1/occurrence/search?taxonKey={TAXON_ID}"

def fetch_species_data():
    """
    Fetches species data from the GBIF API.
    """
    response = requests.get(SPECIES_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch species data for taxonID {TAXON_ID}")
        return None

def fetch_occurrence_data():
    """
    Fetches occurrence data for the species from the GBIF API.
    """
    response = requests.get(OCCURRENCE_URL)
    if response.status_code == 200:
        return response.json()["results"]
    else:
        print(f"Failed to fetch occurrence data for taxonID {TAXON_ID}")
        return []

def write_to_json(data, filename="species_"+str(TAXON_ID)+"_data.json"):
    """
    Writes data to a JSON file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Data written to {filename}")

def main():
    # Fetch species data
    species_data = fetch_species_data()
    if not species_data:
        return

    # Fetch occurrence data
    occurrence_data = fetch_occurrence_data()

    # Combine species and occurrence data
    combined_data = {
        "species": species_data,
        "occurrences": occurrence_data
    }

    # Write data to a JSON file
    write_to_json(combined_data)

if __name__ == "__main__":
    main()