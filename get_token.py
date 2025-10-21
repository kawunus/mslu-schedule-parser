from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_PATH = 'credentials.json'
TOKEN_PATH = 'token.json'

def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Файл {CREDENTIALS_PATH} не найден!")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())

    print(f"✅ Токен сохранён в {TOKEN_PATH}. Теперь можно запускать контейнер!")

if __name__ == "__main__":
    main()