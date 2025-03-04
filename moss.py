import requests
import json
import os

# GBIF API endpoint for species data
TAXON_ID = 7459211
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

def get_iucn_data(scientific_name):
    """
    Fetches the URL to the conservation assessment for a species from the IUCN Red List API v4.
    
    Args:
        scientific_name (str): The scientific name of the species (e.g., "Polytrichum commune").
    
    Returns:
        str: The URL to the conservation assessment, or None if not found.
    """
    # Get the API key from environment variables
    api_key = os.getenv("IUCN_API_KEY")
    if not api_key:
        raise ValueError("IUCN_API_KEY environment variable not set.")

    # Split the scientific name into genus and species
    genus_species = scientific_name.split()

    # Base URL for the IUCN Red List API v4
    url = f"https://api.iucnredlist.org/api/v4/taxa/scientific_name?genus_name={genus_species[0]}&species_name={genus_species[1]}"
    
    # Headers including the Authorization header
    headers = {
        "accept": "application/json",
        "Authorization": api_key,
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the response JSON
        data = response.json()
        
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IUCN conservation URL for {scientific_name}: {e}")
        return None

def main():
    # Fetch species data
    species_data = fetch_species_data()
    if not species_data:
        return

    # Fetch occurrence data
    occurrence_data = fetch_occurrence_data()

    iucn_data = get_iucn_data(species_data["scientificName"])

    # Combine species and occurrence data
    combined_data = {
        "species": species_data,
        "occurrences": occurrence_data,
        "iucn_data": iucn_data
    }

    # Write data to a JSON file
    write_to_json(combined_data)



if __name__ == "__main__":
    main()