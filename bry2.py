import requests
import json

# Path to the file containing taxonomy IDs
TAXON_IDS_FILE = "moss_taxonomy_ids.txt"

processed_ids = None

def read_taxonomy_ids(filename):
    """
    Reads taxonomy IDs from a text file.
    """
    with open(filename, "r") as f:
        taxonomy_ids = [line.strip() for line in f.readlines()]
    return taxonomy_ids

def get_species_data(taxon_id):
    """
    Fetches species data from the GBIF API.
    If the species is a synonym, attempts to find the accepted name.
    Checks if the acceptedKey is already in the processed_ids list to avoid loops.
    """
    global processed_ids
    if processed_ids is None:
        processed_ids = set()  # Initialize a set to track processed IDs

    # Check if this taxon_id has already been processed
    if taxon_id in processed_ids:
        print(f"Species ID {taxon_id} has already been processed. Skipping to avoid loops.")
        return None

    # Add the current taxon_id to the set of processed IDs
    processed_ids.add(taxon_id)

    url = f"https://api.gbif.org/v1/species/{taxon_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        # Check if the species is a synonym
        taxonomic_status = data.get("taxonomicStatus", "").lower()
        if "synonym" in taxonomic_status:
            accepted_key = data.get("acceptedKey")
            if accepted_key:
                print(f"Species {data.get('scientificName', 'Unknown')} is a synonym. Fetching accepted name...")
                return get_species_data(accepted_key)  # Recursively fetch the accepted name
            else:
                print(f"Skipping synonym without an accepted name: {data.get('scientificName', 'Unknown')}")
                return None
        
        # If the species is accepted, return its data
        return {
            "taxonID": taxon_id,
            "species": data.get("species", "Unknown"),
            "genus": data.get("genus", "Unknown"),
            "scientificName": data.get("scientificName", "Unknown"),
            "vernacularName": data.get("vernacularName", "Unknown")
        }
    else:
        print(f"Failed to fetch data for species ID {taxon_id}")
        return None

def get_occurrence_data(taxon_id, limit=5):
    """
    Fetches occurrence data for a given species ID from the GBIF API.
    """
    url = f"https://api.gbif.org/v1/occurrence/search?taxonKey={taxon_id}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["results"]
    else:
        print(f"Failed to fetch occurrences for species ID {taxon_id}")
        return []

def extract_habitats(occurrences):
    """
    Extracts a list of unique habitats (e.g., countries) from occurrence data.
    """
    habitats = set()
    for occurrence in occurrences:
        country = occurrence.get("country", "Unknown")
        if country != "Unknown":
            habitats.add(country)
    return list(habitats)

def is_valid_species(species_info):
    """
    Checks if a species entry is valid (i.e., not a placeholder name).
    """
    scientific_name = species_info.get("scientificName", "")
    # Exclude names that are codes (e.g., start with "SH" or contain numbers)
    return not (scientific_name.startswith("SH") or any(char.isdigit() for char in scientific_name))

def write_to_json(data, filename="moss_species_data.json"):
    """
    Writes data to a JSON file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Data written to {filename}")

import os
import requests

def get_iucn_conservation_url(scientific_name):
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
        
        # Check if the species data is available
        if "assessments" in data and data["assessments"]:
            # Get the assessment URL
            assessment_url = data["assessments"][0]["url"]
            return assessment_url
        else:
            print(f"No assessments found for {scientific_name}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IUCN conservation URL for {scientific_name}: {e}")
        return None

def main():
    # Read taxonomy IDs from the file
    taxonomy_ids = read_taxonomy_ids(TAXON_IDS_FILE)

    if not taxonomy_ids:
        print("No taxonomy IDs found. Exiting.")
        return

    # Limit to the first 20 species
    taxonomy_ids = taxonomy_ids[:100]

    # Fetch data for each species
    species_data = []
    for taxon_id in taxonomy_ids:
        # Get species data
        species_info = get_species_data(taxon_id)
        if not species_info:
            continue

        # Skip placeholder names
        if not is_valid_species(species_info):
            print(f"Skipping placeholder species: {species_info['scientificName']}")
            continue

        # Get IUCN conservation URL
        conservation_url = None
        if len(species_info["scientificName"].split()) > 2:
            conservation_url = get_iucn_conservation_url(species_info["scientificName"])
        species_info["conservation_url"] = conservation_url

        # Get occurrence data
        occurrences = get_occurrence_data(taxon_id)
        #species_info["occurrences"] = occurrences

        # Extract habitats from occurrences
        habitats = extract_habitats(occurrences)
        species_info["habitats"] = habitats

        # Add to the list
        species_data.append(species_info)

    # Write the data to a JSON file
    write_to_json(species_data)

if __name__ == "__main__":
    main()