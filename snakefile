configfile: os.path.join(workflow.basedir, "config.yaml")
containerized: config["containerized"]
from datetime import date
from glob import glob

rule all:
    input:
        'results/lineage_notes.txt',
        'results/lineage_notes_expanded.csv'

rule fetch_lineage_notes:
    output: 
        notes="results/lineage_notes.txt"
    params: 
        url=config["fetch_lineage_notes"]["url"]
    shell:
        """
        curl -L {params.url} -o {output.notes}
        """

rule expand_lineages:
    input:
        notes="results/lineage_notes.txt"
    output:
        expanded="results/lineage_notes_expanded.csv"
    shell:
        """
        python3 expand_lineages.py --input {input.notes} \
            --output {output.expanded}
        """
    