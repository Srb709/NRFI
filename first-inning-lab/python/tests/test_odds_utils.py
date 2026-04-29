from first_inning_lab.utils.odds import *
def test_odds():
    assert round(american_to_implied_probability(-110),3)==0.524
    fair=remove_vig_two_way(-110,-110)
    assert round(fair['nrfi_fair_probability'],2)==0.5
    assert round(calculate_edge(0.56,0.5),2)==0.06
