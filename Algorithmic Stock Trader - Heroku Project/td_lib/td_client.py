from td_lib.td_secrets.config import *
from td.client import TDClient



td_session = TDClient(client_id=TD_CONSUMER_KEY, redirect_uri=REDIRECT_URI, credentials_path=CREDENTIAL_PATH, account_number=TD_ACCOUNT_NUMBER)



