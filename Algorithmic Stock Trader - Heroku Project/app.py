import firebase_admin
from firebase_admin import credentials
from flask import Flask, request, Response
from td_lib.td_client import *
from td_lib.order_presets.options import getters
import os
import pprint
from firebase_admin import firestore

app = Flask(__name__)
firebase_cred = credentials.Certificate("secrets/algorithmic-stock-trader-1b0ce-firebase-adminsdk-ay42q-7fdf21af79.json")
firebase_admin.initialize_app(firebase_cred)
port = int(os.environ.get('PORT', 33507))
db = firestore.client()
rsi_option_balance_doc_ref = db.collection("Balance").document ("rsi_algo")

# TODO: make sure to cancel any outstanding orders before making a new one


@app.route("/")
def index():
    print("Someone has accessed the index file")
    return "This is a simple algorithmic trading software"

@app.route("/api/alerts/rsi", methods=["POST"])
def handle_rsi_webhook():
    print("rsi webhook received")
    s = request.get_json()
    print(s)
    rsiAlertValue = s["alert"]
    if rsiAlertValue == "SELL SPY":
        portfolio_call_option_stream = db.collection("Portfolio").document("spy_rsi_option_algo").collection("current_calls").stream()
        for option_doc in portfolio_call_option_stream:
            doc_id = option_doc.id
            option_doc = option_doc.to_dict()
            balanceToAdd = 0
            optionName = doc_id
            num_contracts = option_doc["num_contracts"]
            optionQuote = td_session.get_quotes(instruments=[optionName])
            if optionQuote is None:
                optionQuote = td_session.get_quotes(instruments=[optionName])
            balanceToAdd += ((optionQuote[optionName]["bidPrice"] * 100 + optionQuote[optionName]["askPrice"] * 100)/2) * num_contracts
            sellTransaction = {
                "transaction_type": "SELL",
                "assetType": "OPTION",
                "optionType": "CALL",
                "description": optionQuote[optionName]["description"],
                "symbol": optionName,
                "date": firestore.firestore.SERVER_TIMESTAMP,
                "num_contracts": num_contracts,
                "total": "+" + str(balanceToAdd)
            }
            db.collection("Trades").add(sellTransaction)
            db.collection("Portfolio").document("spy_rsi_option_algo").collection("current_calls").document(optionName).delete()
            db.collection("Portfolio").document("spy_rsi_option_algo").update({
                "calls": firestore.firestore.Increment(-1 * num_contracts),
                "balance": firestore.firestore.Increment(balanceToAdd)
            })
        put_option_chain = td_session.get_options_chain(getters.getPutConfig("SPY"))
        if put_option_chain is None:
            put_option_chain = td_session.get_options_chain(getters.getPutConfig("SPY"))
        stock_price = put_option_chain["underlying"]["last"]
        for date in put_option_chain["putExpDateMap"].values():
            for strike in date.keys():
                if float(strike) - 1.5 >= stock_price:
                    option_symbol = date[strike][0]["symbol"]
                    option_description = date[strike][0]["description"]
                    option_type = date[strike][0]["putCall"]
                    num_contracts = 5
                    option_price = (date[strike][0]["ask"] * 100 + date[strike][0]["bid"] * 100)/2
                    total_cost = option_price * num_contracts
                    buyTransaction = {
                        "transaction_type": "BUY",
                        "assetType": "OPTION",
                        "optionType": option_type,
                        "symbol": option_symbol,
                        "description": option_description,
                        "date": firestore.firestore.SERVER_TIMESTAMP,
                        "num_contracts": num_contracts,
                        "total": "-" + str(total_cost)
                    }
                    db.collection("Trades").add(buyTransaction)
                    db.collection("Portfolio").document("spy_rsi_option_algo").collection("current_puts").document(option_symbol).set({
                        "symbol": option_symbol,
                        "description": option_description,
                        "num_contracts": num_contracts,
                        "total_cost": total_cost
                    })
                    db.collection("Portfolio").document("spy_rsi_option_algo").update({
                        "puts": firestore.firestore.Increment(num_contracts),
                        "balance": firestore.firestore.Increment(-1*total_cost)
                    })
                    return Response(status=200)



    elif rsiAlertValue == "BUY SPY":
        portfolio_put_option_stream = db.collection("Portfolio").document("spy_rsi_option_algo").collection(
            "current_puts").stream()
        for option_doc in portfolio_put_option_stream:
            doc_id = option_doc.id
            option_doc = option_doc.to_dict()
            balanceToAdd = 0
            optionName = doc_id
            num_contracts = option_doc["num_contracts"]
            optionQuote = td_session.get_quotes(instruments=[optionName])
            if optionQuote is None:
                optionQuote = td_session.get_quotes(instruments=[optionName])
            balanceToAdd += ((optionQuote[optionName]["bidPrice"] * 100 + optionQuote[optionName][
                "askPrice"] * 100) / 2) * num_contracts
            sellTransaction = {
                "transaction_type": "SELL",
                "assetType": "OPTION",
                "optionType": "PUT",
                "description": optionQuote[optionName]["description"],
                "symbol": optionName,
                "date": firestore.firestore.SERVER_TIMESTAMP,
                "num_contracts": num_contracts,
                "total": "+" + str(balanceToAdd)
            }
            db.collection("Trades").add(sellTransaction)
            db.collection("Portfolio").document("spy_rsi_option_algo").collection("current_puts").document(
                optionName).delete()
            db.collection("Portfolio").document("spy_rsi_option_algo").update({
                "puts": firestore.firestore.Increment(-1 * num_contracts),
                "balance": firestore.firestore.Increment(balanceToAdd)
            })
        call_option_chain = td_session.get_options_chain(getters.getCallConfig("SPY"))
        if call_option_chain is None:
            call_option_chain = td_session.get_options_chain(getters.getCallConfig("SPY"))
        stock_price = call_option_chain["underlying"]["last"]
        for date in call_option_chain["callExpDateMap"].values():
            for strike in date.keys():
                if float(strike) + 1.5 <= stock_price:
                    option_symbol = date[strike][0]["symbol"]
                    option_description = date[strike][0]["description"]
                    option_type = date[strike][0]["putCall"]
                    num_contracts = 5
                    option_price = (date[strike][0]["ask"] * 100 + date[strike][0]["bid"] * 100) / 2
                    total_cost = option_price * num_contracts
                    buyTransaction = {
                        "transaction_type": "BUY",
                        "assetType": "OPTION",
                        "optionType": option_type,
                        "symbol": option_symbol,
                        "description": option_description,
                        "date": firestore.firestore.SERVER_TIMESTAMP,
                        "num_contracts": num_contracts,
                        "total": "-" + str(total_cost)
                    }
                    db.collection("Trades").add(buyTransaction)
                    db.collection("Portfolio").document("spy_rsi_option_algo").collection("current_calls").document(option_symbol).set({
                        "symbol": option_symbol,
                        "description": option_description,
                        "num_contracts": num_contracts,
                        "total_cost": total_cost
                    })
                    db.collection("Portfolio").document("spy_rsi_option_algo").update({
                        "calls": firestore.firestore.Increment(num_contracts),
                        "balance": firestore.firestore.Increment(-1*total_cost)
                    })
                    return Response(status=200)


def main():

    # creating a td ameritrade session
    td_session.login()
    '''
    spy_option_chain = td_session.get_options_chain(option_chain=getPutConfig("SPY"))
    pprint.pp(spy_option_chain)'''

    # run server to receive rsi alert webhooks from trading view
    print(f"app running on port {port}")
    app.run(port=port)



if __name__ == "__main__":
    main()


