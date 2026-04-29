def american_to_implied_probability(odds:int)->float:
    return 100/(odds+100) if odds>0 else (-odds)/((-odds)+100)

def remove_vig_two_way(nrfi_odds:int, yrfi_odds:int)->dict:
    p1=american_to_implied_probability(nrfi_odds); p2=american_to_implied_probability(yrfi_odds); t=p1+p2
    return {'nrfi_fair_probability': p1/t,'yrfi_fair_probability': p2/t}

def calculate_edge(model_probability:float, market_probability:float)->float:
    return model_probability-market_probability
