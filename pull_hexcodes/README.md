## Overview

This script pulls hex code colors from [CDC strain surveillance's tableau dashboard](https://public.tableau.com/app/profile/strain.surv/viz/Variant_Proportions_Plus_Nowcasting_PREVIEW/BarchartOnly).

It will 

- request the dashboard from the web page
- download the `.twb` file and the underlying `.xml`
- parse the `.xml` which contains the assigned colors for each variant
- write the output of variant/assigned color to a `parsed_hexcodes.csv` file in this folder

## For devs

To get the downloaded file, I used dev tools in a web browser (right click > Inspect),
and then in the Network tab it will show what the file path is when you click Download on 
the tableau dashboard. 

That file path can be used in python to automatically pull the dashboard 
(instead of manually going to the website and downloading it yourself).

### Requests

Like this: 

```python
import requests

url = "https://public.tableau.com/workbooks/Variant_Proportions_Plus_Nowcasting_PREVIEW.twb"
response = requests.get(url)
response.raise_for_status()

twb_file = "Variant_Proportions_Plus_Nowcasting_PREVIEW.twb"

with open(twb_file, "wb") as f:
    f.write(response.content)
```

It's a zip file, so unzip it with this:

```python
with zipfile.ZipFile(twb_file, "r") as z:
    # find the .twb inside
    twb_names = [n for n in z.namelist() if n.endswith(".twb")]
    print("Found TWB files:", twb_names)

    inner_twb = twb_names[0]

    # read XML content
    xml_bytes = z.read(inner_twb)
```
### Parsing the XML

To parse the XML i'm using [beautifulsoup](https://pypi.org/project/beautifulsoup4/)

```python
# Now parse with BeautifulSoup
soup = BeautifulSoup(xml_bytes, "xml")

```

If you want to examine the XML, run this:

```python
with open("workbook_pretty.xml", "w", encoding="utf-8") as f:
    f.write(soup.prettify())

```

Now to parse the text you need to look for certain tags. Honestly, AI helped me with this. 
The tags look like this, where `<map> </map>` assigns the color by `<bucket>`, 
like it wraps the variant in a mapped color:

```xml
<map to="#006064">
<multibucket>
<bucket>
    "VOC"
</bucket>
<bucket>
    "BQ.1"
</bucket>
</multibucket>
</map>
```

In the example above, `BQ.1` is mapped to the hex color code `#006064`.

So now to get all the assigned colors + variants, loop through the tags like this:

- get all `map` tags
- within the `map`, get the hex codes from the `to = ` tag
- select `multibucket`, and `bucket`, and the names are within each `bucket`

```python
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
```

### Output to csv

Now we have the variant names and colors associated with the names. Put them into 
a polars dataframe and write to csv:

```python
# create Polars DataFrame
df = (
    pl.DataFrame(data, schema=["variant", "color"], orient='row')
    # remove rows where the variant is Top or VOC, those don't appear to be variants
    .filter(~pl.col('variant').is_in(["Top","VOC"]))
)

df.write_csv("parsed_hexcodes.csv")
```

## To run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/)

Make a .venv

```bash
uv venv
```

Then install the packages with

```bash
uv sync
```

