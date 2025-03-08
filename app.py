from flask import Flask, render_template, request, jsonify
import itertools

app = Flask(__name__)

def american_to_decimal(odds):
    """Convert American odds to decimal format."""
    if odds > 0:
        return 1 + (odds / 100)
    elif odds < 0:
        return 1 + (100 / abs(odds))
    return 1  # Default

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate_parlays", methods=["POST"])
def generate_parlays():
    data = request.json
    unit_size = float(data["unitSize"])
    teams = data["teams"]

    # Parse teams into structured format [(team_name, odds)]
    cbb_teams = [tuple(team.split(",")) for team in teams["cbb"] if "," in team]
    nba_teams = [tuple(team.split(",")) for team in teams["nba"] if "," in team]
    nhl_teams = [tuple(team.split(",")) for team in teams["nhl"] if "," in team]

    # Convert odds to float
    cbb_teams = [(name.strip(), float(odds.strip())) for name, odds in cbb_teams]
    nba_teams = [(name.strip(), float(odds.strip())) for name, odds in nba_teams]
    nhl_teams = [(name.strip(), float(odds.strip())) for name, odds in nhl_teams]

    # Calculate total number of parlays
    total_parlays = len(cbb_teams) * len(nba_teams) * len(nhl_teams)
    capital = unit_size * total_parlays

    # Generate all possible parlays
    parlays = []
    for cbb, nba, nhl in itertools.product(cbb_teams, nba_teams, nhl_teams):
        cbb_name, cbb_odds = cbb
        nba_name, nba_odds = nba
        nhl_name, nhl_odds = nhl

        # Convert odds to decimal
        cbb_dec = american_to_decimal(cbb_odds)
        nba_dec = american_to_decimal(nba_odds)
        nhl_dec = american_to_decimal(nhl_odds)

        # Calculate total parlay odds
        parlay_dec = cbb_dec * nba_dec * nhl_dec
        parlay_american = round((parlay_dec - 1) * 100) if parlay_dec >= 2 else round(-100 / (parlay_dec - 1))

        # Compute payoff
        payoff = float(f"{round((parlay_american / 100) * unit_size - capital+unit_size, 2):.2f}")

        implied_prob = round((100/(parlay_american+100))*100,2)


        parlays.append([cbb_name, cbb_odds, nba_name, nba_odds, nhl_name, nhl_odds, parlay_american, f"{round(implied_prob, 2):.2f}%", payoff])

    # Sort parlays by total odds
    parlays.sort(key=lambda x: x[6])

    loss_count = 0
    win_count = 0
    min_payoff = 10e112
    max_payoff = -10e12
    total = 0
    rolling_ev = 0
    for i in range(len(parlays)):
        item_row = parlays[i]
        row_payoff = item_row[8]

        ip = float(item_row[7].strip("%"))/100

        rolling_ev+=ip*row_payoff

        total += row_payoff
        if row_payoff < 0:
            loss_count += 1
        else:
            win_count += 1

        if row_payoff <+ min_payoff:
            min_payoff = row_payoff
        if row_payoff >= max_payoff:
            max_payoff = row_payoff

    average = int(((total/len(parlays))*(100/len(parlays))/capital))
    return_val = (rolling_ev/capital)*100


    return jsonify({"parlays": parlays, "totalParlays": total_parlays, "capital": capital, "loss_count": loss_count, "win_count": win_count, "min_payoff":min_payoff, "max_payoff": max_payoff, "average": average, "rolling_ev": round(rolling_ev,2), "return_val": f"{round(return_val, 2):.2f}%"})

if __name__ == "__main__":
    app.run(debug=True)

