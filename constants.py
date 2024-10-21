import os
from dotenv import load_dotenv


load_dotenv()

AZURE_DB_PW_DEV = os.getenv("AZURE_DB_PW_DEV")
AZURE_DB_PW_PROD = os.getenv("AZURE_DB_PW_PROD")

MODE = os.getenv("MODE", "dev")
pwd = os.getenv("APP_PWD")
uid = os.getenv("APP_UID")
