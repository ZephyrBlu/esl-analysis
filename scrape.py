import re
from requests_html import AsyncHTMLSession


REGIONS = ['AM', 'EU', 'KR']
URL = 'https://liquipedia.net/starcraft2/ESL_Open_Cup_'
RACES = ['Protoss', 'Terran', 'Zerg']
BACKGROUND_COLOURS = {
    'rgb(221, 244, 221)': 'Protoss',
    'rgb(251, 223, 223)': 'Zerg',
    'rgb(222, 227, 239)': 'Terran',
}
matchup_win_loss = {}
for race in RACES:
    matchup_win_loss[race] = {}
    for race_inner in RACES:
        matchup_win_loss[race][race_inner] = {
            'win': 0,
            'loss': 0,
        }


def generate_requests(start_num, end_num=None):
    if not start_num or type(start_num) not in [list, int]:
        raise TypeError('The first argument must be an int or list of ints')

    if type(start_num) == list and end_num:
        raise ValueError('Cannot specify both a list and a range of numbers')

    numbers = start_num

    if type(start_num) == int:
        numbers = [start_num]

    if end_num:
        numbers = [i for i in range(start_num, end_num + 1)]

    # numbers should always have a value
    assert numbers, 'Something went wrong'

    functions = []
    for number in numbers:
        for region in REGIONS:
            async def fetch_page(region=region, number=number):
                response = await session.get(f'{URL}{region}/{number}')
                return response
            functions.append(fetch_page)
    return functions


session = AsyncHTMLSession()
results = session.run(*generate_requests(61))
for page in results:
    games = page.html.find('.bracket-game')
    for game in games:
        players = {}
        p_id = 0

        # need very specific selector to prevent bracket-popup elements from being included
        for player_cell in game.find('div.bracket-game > div > div:first-child'):
            if 'bracket-popup' in player_cell.attrs['class']:
                continue

            # increment p_id after checking for invalid elements
            p_id += 1

            cell_style = player_cell.attrs['style']
            cell_background = re.search('(?<=background:)[^;]*', cell_style)[0]

            # sometimes background can be uncoloured due to a bye
            if cell_background not in BACKGROUND_COLOURS:
                continue

            player_race = BACKGROUND_COLOURS[cell_background]

            # sometimes there is no value for the score
            try:
                score = int(player_cell.find('.bracket-score')[0].text)
            except ValueError:
                continue

            players[p_id] = {
                'race': player_race,
                'score': score,
            }

        # due to bye, there may not always be 2 players
        if len(players) != 2:
            continue

        for p_id, info in players.items():
            player_race = players[p_id]['race']
            player_score = players[p_id]['score']

            opp_id = 1 if p_id == 2 else 2
            opp_race = players[opp_id]['race']

            # score of 0 means there will be no change in wins/losses
            if player_score == 0:
                continue

            matchup_win_loss[player_race][opp_race]['win'] += player_score
            matchup_win_loss[opp_race][player_race]['loss'] += player_score


for ro, ri in matchup_win_loss.items():
    print(ro)
    print('-----')
    for r, v in ri.items():
        total = v['win'] + v['loss']
        winrate = round((v['win'] / total) * 100, 1) if total else 0
        print(f'vs {r} {winrate}% ({v["win"]}/{total})')
    print('\n')
