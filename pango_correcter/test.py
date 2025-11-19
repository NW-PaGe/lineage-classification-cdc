from pango_corrector import corrector
corrector = corrector() # initializing pulls the latest correction keys .json
corrector.check_coverage() # see if any lineages have been withdrawn since last update to the corrector dictionary
corrector.correct("A.8") # input the withdrawn lineage to get the latest assignment, A.9