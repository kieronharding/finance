# Import the required libraries
import requests
import oauthlib
import gspread
import schedule
import time

# Define the open banking API parameters
api_base_url = "https://api.hsbc.com/open-banking/v3.1/aisp" # Change this according to your API provider
client_id = "your_client_id" # Change this according to your API credentials
client_secret = "your_client_secret" # Change this according to your API credentials
redirect_uri = "your_redirect_uri" # Change this according to your API credentials
scope = "accounts balances transactions" # Change this according to your API scope
authorization_endpoint = api_base_url + "/authorize"
token_endpoint = api_base_url + "/token"

# Define the Google Sheets parameters
sheet_id = "your_sheet_id" # Change this according to your Google Sheet ID
sheet_name = "your_sheet_name" # Change this according to your Google Sheet name
credentials_file = "your_credentials_file.json" # Change this according to your Google Sheets credentials file

# Define the schedule parameters
interval = "daily" # Change this according to your desired schedule interval
time_of_day = "12:00" # Change this according to your desired schedule time of day

# Create an OAuth 2.0 session
oauth2_session = oauthlib.oauth2.WebApplicationClient(client_id)

# Get the authorization URL and code
authorization_url, state = oauth2_session.prepare_authorization_request(authorization_endpoint, redirect_uri=redirect_uri, scope=scope)
print("Please go to this URL and authorize access: ", authorization_url)
authorization_response = input("Enter the full callback URL: ")

# Get the access token and refresh token
token = oauth2_session.fetch_token(token_endpoint, authorization_response=authorization_response, client_secret=client_secret)
access_token = token["access_token"]
refresh_token = token["refresh_token"]

# Define a function to refresh the access token
def refresh_access_token():
    global access_token
    global refresh_token
    new_token = oauth2_session.refresh_token(token_endpoint, refresh_token=refresh_token, client_secret=client_secret)
    access_token = new_token["access_token"]
    refresh_token = new_token["refresh_token"]

# Define a function to get the account ID
def get_account_id():
    headers = {"Authorization": "Bearer " + access_token}
    response = requests.get(api_base_url + "/accounts", headers=headers)
    data = response.json()
    account_id = data["Data"]["Account"][0]["AccountId"] # Change this according to your account index
    return account_id

# Define a function to get the latest transaction
def get_latest_transaction(account_id):
    headers = {"Authorization": "Bearer " + access_token}
    response = requests.get(api_base_url + "/accounts/" + account_id + "/transactions", headers=headers)
    data = response.json()
    transaction = data["Data"]["Transaction"][0] # Change this according to your transaction index
    amount = transaction["Amount"]["Amount"]
    currency = transaction["Amount"]["Currency"]
    date = transaction["BookingDateTime"]
    category = transaction["TransactionInformation"]
    return amount, currency, date, category

# Define a function to append a new row to the Google Sheet
def append_to_sheet(amount, currency, date, category):
    gc = gspread.service_account(filename=credentials_file)
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(sheet_name)
    new_row = [amount, currency, date, category]
    ws.append_row(new_row)

# Define a function to run the main logic
def run():
    try:
        account_id = get_account_id()
        amount, currency, date, category = get_latest_transaction(account_id)
        append_to_sheet(amount, currency, date, category)
        print("Successfully updated the Google Sheet with the latest transaction.")
    except Exception as e:
        print("An error occurred: ", e)
        refresh_access_token()
        run()

# Schedule the function to run at a regular interval
schedule.every().interval.at(time_of_day).do(run)

# Run the function once at the start
run()

# Keep the program running
while True:
    schedule.run_pending()
    time.sleep(1)
