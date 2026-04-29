from first_inning_lab.features.first_inning_labels import label_first_inning_runs
def test_labels(): assert label_first_inning_runs(0)=='NRFI' and label_first_inning_runs(1)=='YRFI'
