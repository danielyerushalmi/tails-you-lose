"""Experiment definitions for "Do AI models have money biases?".

Every trial is one fresh, independent conversation — a synthetic "participant" who
sees exactly one version of one problem (between-subjects, like the human studies).

Each experiment has two surfaces:
  classic — the textbook wording (models have almost certainly seen it in training)
  novel   — a financial re-skin with identical structure (unlikely to be memorised)
Comparing the two separates "reasoning" from "reciting the famous answer".

Choice options are defined by semantic key; the runner shuffles their order and
assigns A/B labels per trial so position bias cannot masquerade as a preference.
"""

# ---------------------------------------------------------------- E1 framing
FRAMING = {
    "classic": {
        "stem": (
            "Imagine that the U.S. is preparing for the outbreak of an unusual Asian disease, "
            "which is expected to kill 600 people. Two alternative programs to combat the disease "
            "have been proposed. Assume that the exact scientific estimates of the consequences of "
            "the programs are as follows:"
        ),
        "gain": {
            "sure": "If this program is adopted, 200 people will be saved.",
            "risky": "If this program is adopted, there is a 1/3 probability that 600 people will be saved, and a 2/3 probability that no people will be saved.",
        },
        "loss": {
            "sure": "If this program is adopted, 400 people will die.",
            "risky": "If this program is adopted, there is a 1/3 probability that nobody will die, and a 2/3 probability that 600 people will die.",
        },
        "question": "Which of the two programs would you favor?",
    },
    "novel": {
        "stem": (
            "You manage a $600 million employee pension fund. A sudden credit-market crisis is expected "
            "to wipe out the entire $600 million. Your risk team has designed two emergency hedging plans. "
            "Assume the exact estimates of the consequences of the plans are as follows:"
        ),
        "gain": {
            "sure": "If this plan is adopted, $200 million of the fund will be saved.",
            "risky": "If this plan is adopted, there is a 1/3 probability that the full $600 million will be saved, and a 2/3 probability that nothing will be saved.",
        },
        "loss": {
            "sure": "If this plan is adopted, $400 million of the fund will be lost.",
            "risky": "If this plan is adopted, there is a 1/3 probability that nothing will be lost, and a 2/3 probability that the full $600 million will be lost.",
        },
        "question": "Which of the two plans would you choose?",
    },
}

# ---------------------------------------------------------------- E2 loss aversion
LOSS_X = [50, 100, 125, 150, 200, 250, 300, 400, 600]
LOSS_AVERSION = {
    "classic": (
        "You are offered a gamble on the toss of a fair coin. If the coin shows tails, you lose $100. "
        "If the coin shows heads, you win ${x}. Would you accept this gamble?"
    ),
    # v2 (used for all reported results): a neutral trade, no social relationship
    "novel": (
        "Your brokerage app offers you a one-time trade. You stake $100. There is a 50% chance the trade "
        "loses and you lose your $100, and a 50% chance it wins and you get your $100 back plus ${x} in profit. "
        "Nothing else about your finances changes either way. Would you make the trade?"
    ),
    # v1 (exploratory, reported separately as the "friend" variant): the same bet framed as a friend's business.
    # A pilot showed this social cue pushes fast answers toward accepting even the negative-EV $50 bet.
    "friend": (
        "A friend is raising money for a small business and offers you a one-time deal. You put in $100. "
        "There is a 50% chance the business fails and you lose your $100, and a 50% chance it succeeds "
        "and you get your $100 back plus ${x} in profit. Nothing else about your finances changes either way. "
        "Would you take the deal?"
    ),
    "options": {
        "accept": "Accept",
        "decline": "Decline",
    },
}

# ---------------------------------------------------------------- E3 anchoring
ANCHORS = {"none": None, "low": 10, "high": 150}
ANCHORING = {
    # classic: Tversky & Kahneman (1974) wheel-of-fortune UN question
    "classic": {
        "anchor_line": "A wheel of fortune with numbers from 0 to 100 was just spun in front of you and landed on {a}.",
        "compare": "Is the percentage of African countries in the United Nations higher or lower than {a}%?",
        "estimate": "What is your best estimate of the percentage of African countries in the United Nations?",
        "unit": "percent",
    },
    "novel": {
        "context": (
            "Harlow Precision Tools is a mid-sized, profitable U.S. manufacturer of industrial cutting tools. "
            "Last year it earned $2.40 per share. Comparable companies trade at between 12 and 25 times earnings. "
            "Its growth outlook is modest and steady."
        ),
        "anchor_line": "Before you answer, a random number generator produced the number {a}.",
        "compare": "Is the fair value of one Harlow share higher or lower than ${a}?",
        "estimate": "What is your best estimate of the fair value of one Harlow share, in dollars?",
        "unit": "dollars",
    },
}

# ---------------------------------------------------------------- E4 sunk cost
SUNK_COST = {
    # classic: Arkes & Blumer (1985) radar-blank plane
    "classic": {
        "sunk": (
            "As the president of an airline company, you have invested 10 million dollars of the company's money "
            "into a research project. The purpose was to build a plane that would not be detected by conventional "
            "radar, in other words, a radar-blank plane. When the project is 90% completed, another firm begins "
            "marketing a plane that cannot be detected by radar. Also, it is apparent that their plane is much faster "
            "and far more economical than the plane your company is building. The question is: should you invest the "
            "last 1 million dollars of your research funds to finish your radar-blank plane?"
        ),
        "control": (
            "As president of an airline company, you have received a suggestion from one of your employees. The "
            "suggestion is to use the last 1 million dollars of your research funds to develop a plane that would not "
            "be detected by conventional radar, in other words, a radar-blank plane. However, another firm has just "
            "begun marketing a plane that cannot be detected by radar. Also, it is apparent that their plane is much "
            "faster and far more economical than the plane your company could build. The question is: should you "
            "invest the last million dollars of your research funds to build the radar-blank plane proposed by your employee?"
        ),
    },
    "novel": {
        "sunk": (
            "You are the CEO of a software startup. Over the past two years you have spent $4 million of the company's "
            "money building a restaurant-reservation app. The app is 90% finished. This week, a large competitor launched "
            "a reservation app that is clearly faster, has more features, and is free for restaurants. Finishing your app "
            "would take the last $400,000 of your development budget. Should you spend the $400,000 to finish the app?"
        ),
        "control": (
            "You are the CEO of a software startup. One of your employees suggests using the last $400,000 of your "
            "development budget to build a restaurant-reservation app. However, this week a large competitor launched a "
            "reservation app that is clearly faster, has more features, and is free for restaurants. Should you spend the "
            "$400,000 to build the app your employee proposed?"
        ),
    },
    "options": {"invest": "Yes, spend the money", "stop": "No, do not spend the money"},
}

# ---------------------------------------------------------------- E5 disposition effect
DISPOSITION = {
    "classic": (
        "You own shares of two companies in a regular taxable brokerage account. Each position is currently worth "
        "$10,000. Stock {n1} is {d1} since you bought it. Stock {n2} is {d2} since you bought it. Analysts, and "
        "you, see the future prospects of both companies as equally good. You need $10,000 in cash today for an "
        "unexpected expense, so you must sell one of the two positions entirely. Which one do you sell?"
    ),
    "novel": (
        "Two years ago you started investing your summer-job savings. Today you hold two positions in your taxable "
        "brokerage account, each now worth $10,000: shares of {n1}, which have {v1} 30% since you bought them, and "
        "shares of {n2}, which have {v2} 30% since you bought them. Everything you can find suggests both companies have "
        "equally good prospects from here. Your car's transmission just failed and the repair costs $10,000, so you "
        "have to sell one position completely. Which one do you sell?"
    ),
    "names": {"classic": ("A", "B"), "novel": ("Northfield Energy", "Calloway Foods")},
    "options": {"winner": "Sell {w} (the one that has gained)", "loser": "Sell {l} (the one that has lost)"},
}

# ---------------------------------------------------------------- E6 mental accounting
MENTAL_ACCOUNTING = {
    # classic: Tversky & Kahneman (1981) theater ticket
    "classic": {
        "cash": (
            "Imagine that you have decided to see a play where admission is $10 per ticket. As you enter the theater "
            "you discover that you have lost a $10 bill. Would you still pay $10 for a ticket for the play?"
        ),
        "ticket": (
            "Imagine that you have decided to see a play and paid the admission price of $10 per ticket. As you enter "
            "the theater you discover that you have lost the ticket. The seat was not marked and the ticket cannot be "
            "recovered. Would you pay $10 for another ticket?"
        ),
    },
    "novel": {
        "cash": (
            "You have been looking forward to a concert by your favorite artist. Tickets are $150 and you planned to buy "
            "one at the venue box office, where tickets are still available. When you arrive, you realize a $150 cash "
            "envelope you had set aside fell out of your bag on the train and is gone. You can still afford $150. "
            "Would you buy a $150 ticket for the concert?"
        ),
        "ticket": (
            "You have been looking forward to a concert by your favorite artist. You bought a $150 ticket last week. When "
            "you arrive at the venue, you realize the paper ticket fell out of your bag on the train and is gone; it "
            "cannot be reissued. The box office still has tickets for $150, and you can afford it. "
            "Would you buy another $150 ticket for the concert?"
        ),
    },
    "options": {"buy": "Yes, buy the ticket", "skip": "No, do not buy it"},
}

# ---------------------------------------------------------------- E7 certainty / common ratio
CERTAINTY = {
    # classic: Kahneman & Tversky (1979) Problems 3 and 4
    "classic": {
        "stem": "Choose between the following two options:",
        "certain": {"safe": "$3,000 for sure", "gamble": "An 80% chance to win $4,000 (and a 20% chance of nothing)"},
        "scaled": {"safe": "A 25% chance to win $3,000 (and a 75% chance of nothing)", "gamble": "A 20% chance to win $4,000 (and an 80% chance of nothing)"},
        "question": "Which do you prefer?",
    },
    "novel": {
        "stem": "Your employer lets you pick how your year-end bonus is paid. The two options are:",
        "certain": {"safe": "A guaranteed $3,000 bonus", "gamble": "A performance-pool bonus that pays $4,000 with 80% probability and $0 with 20% probability"},
        "scaled": {"safe": "A raffle entry that pays $3,000 with 25% probability and $0 with 75% probability", "gamble": "A raffle entry that pays $4,000 with 20% probability and $0 with 80% probability"},
        "question": "Which option do you pick?",
    },
}
