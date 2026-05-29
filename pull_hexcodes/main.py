import requests
from bs4 import BeautifulSoup
import polars as pl
import zipfile

def main():
    print("Hello from test-hex-pull!")

    def get_variant_list():
        url = "https://data.cdc.gov/resource/jr58-6ysp.json"
        query = {
            "$query": "SELECT DISTINCT variant"
        }
        response = requests.get(url=url, params=query)
        if response.status_code == 200:
            print("dataset was pulled")
            data = pl.from_dicts(response.json())
            unique_vars = data.unique()
        else:
            print(f"Error: {response.status_code}")
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
        pl.DataFrame(data, schema=["variant", "color"], orient='row')
        # remove rows where the variant is not in the lineage list pulled from dataset
        .filter(pl.col('variant').is_in(lineage_list["variant"].to_list()))

    )

    print(df)

    df.write_csv("parsed_hexcodes.csv")

if __name__ == "__main__":
    main()
