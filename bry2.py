import requests
import json
import os
import re

# Path to the file containing taxonomy IDs
TAXON_IDS_FILE = "moss_taxonomy_ids.txt"

processed_ids = None

def build_taxonomic_hierarchy(species_data):
    """
    Builds a hierarchical data structure for taxonomic relationships.
    """
    taxonomic_hierarchy = {}

    for species in species_data:
        class_name = species.get("class", "Unknown")
        order_name = species.get("order", "Unknown")
        family_name = species.get("family", "Unknown")
        genus_name = species.get("genus", "Unknown")

        # Add class if not already present
        if class_name not in taxonomic_hierarchy:
            taxonomic_hierarchy[class_name] = {}

        # Add order if not already present
        if order_name not in taxonomic_hierarchy[class_name]:
            taxonomic_hierarchy[class_name][order_name] = {}

        # Add family if not already present
        if family_name not in taxonomic_hierarchy[class_name][order_name]:
            taxonomic_hierarchy[class_name][order_name][family_name] = {}

        # Add genus if not already present
        if genus_name not in taxonomic_hierarchy[class_name][order_name][family_name]:
            taxonomic_hierarchy[class_name][order_name][family_name][genus_name] = {}

    return taxonomic_hierarchy

def read_taxonomy_ids(filename):
    """
    Reads taxonomy IDs from a text file.
    """
    with open(filename, "r") as f:
        taxonomy_ids = [line.strip() for line in f.readlines()]
    return taxonomy_ids

def get_species_data(taxon_id, synonym=''):
    """
    Fetches species data from the GBIF API.
    If the species is a synonym, attempts to find the accepted name.
    Checks if the acceptedKey is already in the processed_ids list to avoid loops.
    Returns species data including full taxonomic hierarchy.
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
                return get_species_data(accepted_key, synonym={data.get('scientificName', '')})  # Recursively fetch the accepted name
            else:
                print(f"Skipping synonym without an accepted name: {data.get('scientificName', 'Unknown')}")
                return None
        
        published = data.get("publishedIn", "Unknown")
        match = re.search(r"\b\d{4}\b$", published) # check for date at end of publication
        discovered = ""
        if match:
            discovered = match.group(0)
        if not discovered:
            discovered = re.findall(r"\((\d+)\)", published)
            if len(discovered) > 0:
                discovered = discovered[0]
            else:
                discovered = "Unknown"
        
        return {
            "taxonID": str(taxon_id),
            "species": data.get("species", "Unknown"),
            "genus": data.get("genus", "Unknown"),
            "family": data.get("family", "Unknown"),
            "order": data.get("order", "Unknown"),
            "class": data.get("class", "Unknown"),
            "scientificName": data.get("scientificName", "Unknown"),
            "vernacularName": data.get("vernacularName", "Unknown"),
            "publishedIn": published,
            "discovered": discovered
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
        
        assessment_url = ""
        assessment_year = "Unknown"
        assessment_pe = False
        assessment_peiw = False
        # Check if the species data is available
        if data["assessments"]:
            assessments = data.get("assessments", [])
            latest_assessment = next((a for a in assessments if a.get("latest")), None)
            # Get the assessment URL
            if latest_assessment:
                assessment_url = latest_assessment["url"]
                assessment_year = latest_assessment["year_published"]
                assessment_pe = latest_assessment["possibly_extinct"]
                assessment_peiw = latest_assessment["possibly_extinct_in_the_wild"]
        else:
            print(f"No assessments found for {scientific_name}")
            return None
        
        authority = "Unknown"
        if "taxon" in data and "authority" in data["taxon"] and data["taxon"]["authority"]:
            authority = data["taxon"]["authority"]
        else:
            print(f"No authority found for {scientific_name}")

        main_common_name = "Unknown"
        if "taxon" in data and "common_names" in data["taxon"] and data["taxon"]["common_names"]:
            common_names = data["taxon"].get("common_names", [])
            main_common_name = next((a["name"] for a in common_names if a.get("main")), "Unknown")
        else:
            print(f"No common names found for {scientific_name}")

        """
        synonyms = []
        if "taxon" in data and "synonyms" in data["taxon"] and data["taxon"]["synonyms"]:
            for s in data["taxon"]["synonyms"]:
                synonyms.append(s["name"])
        """

        return  {
                    "assessment_url": assessment_url,
                    "assessment_year": assessment_year,
                    "possibly_extinct": assessment_pe,
                    "possibly_extinct_in_the_wild": assessment_peiw,
                    "authority":authority,
                    "vernacularName": main_common_name
                }
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IUCN conservation URL for {scientific_name}: {e}")
        return None
    
# Function to safely load JSON data
def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {file_path}")
    return None

def main():
    # Read taxonomy IDs from the file
    taxonomy_ids = read_taxonomy_ids(TAXON_IDS_FILE)

    if not taxonomy_ids:
        print("No taxonomy IDs found. Exiting.")
        return

    # Limit to the first 20 species
    taxonomy_ids = taxonomy_ids[:300]

    # Fetch data for each species
    species_data = []
    taxonomic_hierarchy = {}
    # Load species data
    species_data = load_json('moss_species_data.json') or []
    # Load taxonomic hierarchy
    taxonomic_hierarchy = load_json('moss_taxonomic_hierarchy.json') or {}

    i = 0
    j = 0
    for taxon_id in taxonomy_ids:
        # Increment counter
        i+=1
        # Get species data
        species_info = get_species_data(taxon_id, species_data)
        if not species_info:
            continue

        # Skip placeholder names
        if not is_valid_species(species_info):
            print(f"Skipping placeholder species: {species_info['scientificName']}")
            continue

        # Get IUCN conservation URL
        conservation_url = None
        if len(species_info["scientificName"].split()) > 2:
            conservation_data = get_iucn_data(species_info["scientificName"])
        if "vernacularName" not in species_info and conservation_data:
            del conservation_data["vernacularName"]
        if conservation_data:
            species_info.update(conservation_data)

        # Get occurrence data
        occurrences = get_occurrence_data(taxon_id)
        #species_info["occurrences"] = occurrences

        # Extract habitats from occurrences
        habitats = extract_habitats(occurrences)
        species_info["habitats"] = habitats

        if species_info["species"] != "Unknown" and species_info["family"] != "Unknown" and species_info["order"] != "Unknown" and species_info["family"] != "Unknown":
            # Add to the list
            species_data.append(species_info)

            # Build the taxonomic hierarchy
            class_name = species_info.get("class", "Unknown")
            order_name = species_info.get("order", "Unknown")
            family_name = species_info.get("family", "Unknown")
            genus_name = species_info.get("genus", "Unknown")

            if class_name not in taxonomic_hierarchy:
                taxonomic_hierarchy[class_name] = {}
            if order_name not in taxonomic_hierarchy[class_name]:
                taxonomic_hierarchy[class_name][order_name] = {}
            if family_name not in taxonomic_hierarchy[class_name][order_name]:
                taxonomic_hierarchy[class_name][order_name][family_name] = {}
            if genus_name not in taxonomic_hierarchy[class_name][order_name][family_name]:
                taxonomic_hierarchy[class_name][order_name][family_name][genus_name] = {}

            del species_info["class"]
            del species_info["order"]
            del species_info["family"]

            j+=1
            if j % 50 == 0:
                write_to_json(species_data, filename="moss_species_data.json")
                write_to_json(taxonomic_hierarchy, filename="moss_taxonomic_hierarchy.json")
        print("Progress: %.2f" % (i/len(taxonomy_ids)))

    # Write the data to a JSON file
    write_to_json(species_data, filename="moss_species_data.json")
    write_to_json(taxonomic_hierarchy, filename="moss_taxonomic_hierarchy.json")

if __name__ == "__main__":
    main()