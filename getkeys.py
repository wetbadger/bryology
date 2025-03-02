import pandas as pd
import os
import zipfile

# Path to the GBIF Backbone Taxonomy file
TAXON_FILE = "Taxon.tsv"

def download_backbone_taxonomy():
    """
    Downloads the GBIF Backbone Taxonomy file if it doesn't already exist.
    """
    url = "https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip"
    output_file = "backbone.zip"

    if not os.path.exists(TAXON_FILE):
        print("Downloading GBIF Backbone Taxonomy...")
        response = requests.get(url, stream=True)
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete. Extracting Taxon.tsv...")
        with zipfile.ZipFile(output_file, 'r') as zip_ref:
            zip_ref.extract("Taxon.tsv")
        print("Extraction complete.")
    else:
        print("Taxon.tsv already exists. Skipping download.")

def get_all_moss_taxonomy_ids():
    """
    Reads the GBIF Backbone Taxonomy file and retrieves all moss species taxonomy IDs.
    """
    print("Loading GBIF Backbone Taxonomy...")

    # Define the columns we need
    columns = [
        "taxonID", "scientificName", "kingdom", "phylum", "class", "order", "family", "genus"
    ]

    # Read the file with error handling for inconsistent rows
    try:
        df = pd.read_csv(
            TAXON_FILE,
            sep="\t",
            usecols=columns,
            on_bad_lines="skip",  # Skip rows with inconsistent fields
            low_memory=False
        )
    except Exception as e:
        print(f"Error reading Taxon.tsv: {e}")
        return []

    # Filter for moss species (Phylum Bryophyta)
    moss_species = df[df["phylum"] == "Bryophyta"]

    # Extract taxonomy IDs
    taxonomy_ids = moss_species["taxonID"].tolist()

    return taxonomy_ids, moss_species

def write_taxonomy_ids_to_file(taxonomy_ids, filename="moss_taxonomy_ids.txt"):
    """
    Writes taxonomy IDs to a text file.
    """
    with open(filename, "w") as f:
        for taxon_id in taxonomy_ids:
            f.write(f"{taxon_id}\n")
    print(f"Taxonomy IDs written to {filename}")

def main():
    # Download the GBIF Backbone Taxonomy file if it doesn't exist
    download_backbone_taxonomy()

    # Get all moss species taxonomy IDs
    taxonomy_ids, moss_species = get_all_moss_taxonomy_ids()

    if not taxonomy_ids:
        print("No moss species found. Exiting.")
        return

    # Write taxonomy IDs to a file
    write_taxonomy_ids_to_file(taxonomy_ids)

    # Optionally, you can work with the moss_species DataFrame here
    # For example, save it to a CSV file for further analysis
    moss_species.to_csv("moss_species.csv", index=False)
    print("Moss species data saved to moss_species.csv")

if __name__ == "__main__":
    main()