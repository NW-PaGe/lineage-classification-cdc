import requests
from bs4 import BeautifulSoup
import polars as pl
import zipfile


def main():
    print("Hello from test-hex-pull!")

    def get_variant_list():
        print(f" \nGetting variant list from full CDC dataset \n")
        url = "https://data.cdc.gov/resource/jr58-6ysp.json"
        query = {"$query": "SELECT DISTINCT variant"}
        try:
            response = requests.get(url=url, params=query)
            response.raise_for_status
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"The request timed out: {timeout_err}")
        except requests.exceptions.RequestException as err:
            print(f"An unexpected error occurred: {err}")
        else:
            data = pl.from_dicts(response.json())
            unique_vars = data.unique()
            print(f"\t Success! There are {len(unique_vars)} unique variants. \n")
        return unique_vars

    lineage_list = get_variant_list()

    url = "https://public.tableau.com/workbooks/Variant_Proportions_Plus_Nowcasting_PREVIEW.twb"

    response = requests.get(url)
    response.raise_for_status()

    twb_file = "Variant_Proportions_Plus_Nowcasting_PREVIEW.twb"

    with open(twb_file, "wb") as f:
        f.write(response.content)

    with zipfile.ZipFile(twb_file, "r") as z:
        # find the .twb inside
        twb_names = [n for n in z.namelist() if n.endswith(".twb")]
        print("Found TWB files:", twb_names)

        inner_twb = twb_names[0]

        # read XML content
        xml_bytes = z.read(inner_twb)

    # Now parse with BeautifulSoup
    soup = BeautifulSoup(xml_bytes, "xml")
    print("Parsed OK!")

    # collect variant → color
    data = []
    for map_tag in soup.find_all("map"):
        color = map_tag.get("to")
        multibucket = map_tag.find("multibucket")
        if multibucket:
            buckets = multibucket.find_all("bucket")
            for b in buckets:
                name = b.text.strip().strip('"')
                data.append((name, color))

    # create Polars DataFrame
    df = (
        pl.DataFrame(data, schema=["variant", "color"], orient="row")
        # remove rows where the variant is not in the lineage list pulled from dataset
        .filter(pl.col("variant").is_in(lineage_list["variant"].to_list()))
    )

    print(df)

    df.write_csv("parsed_hexcodes.csv")


if __name__ == "__main__":
    main()