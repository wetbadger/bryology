import requests
import json

def get_moss_species_data(limit=10):
    # GBIF API endpoint for species search
    url = "https://api.gbif.org/v1/species/search"
    
    # Parameters for the search
    params = {
        "phylumKey": 35,  # Phylum Bryophyta (key for Bryophyta in GBIF)
        "rank": "SPECIES",  # Filter to species rank
        "limit": limit,     # Limit to the first 10 results
        "status": "ACCEPTED"  # Only include accepted names
    }

    # Make the API request
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from GBIF API: {response.status_code}")

    # Parse the response JSON
    species_data = response.json()['results']

    # Fetch occurrence data for each species
    occurrence_data = []
    for species in species_data:
        species_key = species['key']
        occurrences_url = f"https://api.gbif.org/v1/occurrence/search?taxonKey={species_key}&limit=5"
        occurrences_response = requests.get(occurrences_url)
        if occurrences_response.status_code == 200:
            occurrences = occurrences_response.json()['results']
            occurrence_data.append({
                'species_key': species_key,
                'scientificName': species.get('scientificName', 'N/A'),
                'occurrences': occurrences
            })
        else:
            print(f"Failed to fetch occurrences for species {species_key}")

    return species_data, occurrence_data

def write_to_json(data, filename='moss_data.json'):
    # Write data to a JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Data written to {filename}")

def main():
    # Get data for the first 10 moss species
    species_data, occurrence_data = get_moss_species_data()

    # Combine species and occurrence data into a single dictionary
    combined_data = {
        'species': species_data,
        'occurrences': occurrence_data
    }

    # Write the combined data to a JSON file
    write_to_json(combined_data)

if __name__ == "__main__":
    main()