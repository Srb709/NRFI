from first_inning_lab.content.x_post_generator import generate_posts


def test_content_blocks_and_guardrails():
    board = [{'game': 'Demo A @ Demo B', 'public_label': 'Clean First Frame', 'lean': 'NRFI'}]
    posts = generate_posts(board)
    expected = {'dailyBoard','cleanSetupPost','yrfiSmokePost','trapWatchPost','resultsRecapTemplate','discord'}
    assert expected.issubset(set(posts.keys()))
    banned = ['guaranteed winner','lock','max bet','hammer','mortgage','free money','can’t lose','cant lose','risk-free','risk free','sure thing']
    full_text = ' '.join(posts.values()).lower()
    for phrase in banned:
        assert phrase not in full_text
