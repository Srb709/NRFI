from first_inning_lab.content.x_post_generator import generate_daily_board
def test_content(): txt=generate_daily_board([]); assert 'No locks. Just the board.' in txt
