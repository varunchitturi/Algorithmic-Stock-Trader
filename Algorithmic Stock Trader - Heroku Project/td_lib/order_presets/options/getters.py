from datetime import timedelta, date


def dateStringFromDelta(days):
    return (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")


# CALLS

def getCallConfig(symbol, strikeCount=5, daysFromCurrent=10):
    return {
        "symbol": symbol,
        "contractType": "CALL",
        "optionType": "S",
        "strikeCount": strikeCount,
        "includeQuotes": True,
        "strategy": "SINGLE",
        "fromDate": dateStringFromDelta(daysFromCurrent),
        "toDate": dateStringFromDelta(45)

    }


# PUTS

def getPutConfig(symbol,strikeCount=5, daysFromCurrent=10):
    return {
        "symbol": symbol,
        "contractType": "PUT",
        "optionType": "S",
        "strikeCount": strikeCount,
        "includeQuotes": True,
        "strategy": "SINGLE",
        "fromDate": dateStringFromDelta(daysFromCurrent),
        "toDate": dateStringFromDelta(45)

    }
