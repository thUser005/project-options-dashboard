def match_options(options, criteria):
    matches = []

    for opt in options:
        if (
            criteria["index"] in opt["index"] and
            opt["expiry"] == criteria["expiry"] and
            opt["strike"] == criteria["strike"] and
            opt["option_type"] == criteria["option_type"]
        ):
            matches.append(opt)

    return matches
