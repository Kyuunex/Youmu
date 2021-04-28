import os
from youmu.modules.storage_management import dirs


if os.environ.get('YOUMU_TOKEN'):
    bot_token = os.environ.get('YOUMU_TOKEN')
else:
    try:
        with open(dirs.user_data_dir + "/token.txt", "r+") as token_file:
            bot_token = token_file.read().strip()
    except FileNotFoundError as e:
        print("i need a bot token. either set YOUMU_TOKEN environment variable")
        print("or put it in token.txt in my AppData/.config folder")
        raise SystemExit

if os.environ.get('YOUMU_OSU_API_KEY'):
    osu_api_key = os.environ.get('YOUMU_OSU_API_KEY')
else:
    try:
        with open(dirs.user_data_dir + "/osu_api_key.txt", "r+") as token_file:
            osu_api_key = token_file.read().strip()
    except FileNotFoundError as e:
        print("i need a osu api key. either set YOUMU_OSU_API_KEY environment variable")
        print("or put it in token.txt in my AppData/.config folder")
        raise SystemExit

if os.environ.get('YOUMU_CLIENT_ID'):
    client_id = os.environ.get('YOUMU_CLIENT_ID')
else:
    try:
        with open(dirs.user_data_dir + "/client_id.txt", "r+") as token_file:
            client_id = token_file.read().strip()
    except FileNotFoundError as e:
        print("i need a osu web client id. either set YOUMU_CLIENT_ID environment variable")
        print("or put it in token.txt in my AppData/.config folder")
        raise SystemExit

if os.environ.get('YOUMU_CLIENT_SECRET'):
    client_secret = os.environ.get('YOUMU_CLIENT_SECRET')
else:
    try:
        with open(dirs.user_data_dir + "/client_secret.txt", "r+") as token_file:
            client_secret = token_file.read().strip()
    except FileNotFoundError as e:
        print("i need a osu web client secret. either set YOUMU_CLIENT_SECRET environment variable")
        print("or put it in token.txt in my AppData/.config folder")
        raise SystemExit
