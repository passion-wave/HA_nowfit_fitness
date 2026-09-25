"""Constants for the NowFit integration."""

from datetime import timedelta

DOMAIN = "nowfit"
NAME = "NowFit"
VERSION = "2.0.0"

BASE_URL = "https://nowfit.memberarea.club"
ALLOWED_HOST = "nowfit.memberarea.club"
OCCUPANCY_PATH = "/CheckinCounter/GetClubsCheckinCounterPage"
LOGIN_PATH = "/Account/Login"
ACCOUNT_PATH = "/Person/MyAccount"
HISTORY_PATH = "/Person/GetShowMyTrainingTimesPage"

ENTRY_PUBLIC = "public"
ENTRY_MEMBER = "member"
CONF_ENTRY_TYPE = "entry_type"
CONF_CLUB_ID = "club_id"
CONF_CLUB_NAME = "club_name"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_STORE_PASSWORD = "store_password"
CONF_DISPLAY_NAME = "display_name"
CONF_MIN_DURATION = "minimum_duration"
CONF_TIME_ZONE = "time_zone"

PUBLIC_INTERVAL = timedelta(minutes=5)
ACCOUNT_INTERVAL = timedelta(minutes=30)
HISTORY_INTERVAL = timedelta(minutes=15)
PUBLIC_STALE_AFTER = timedelta(minutes=15)
ACCOUNT_STALE_AFTER = timedelta(minutes=90)
HISTORY_STALE_AFTER = timedelta(minutes=45)
REFRESH_COOLDOWN = timedelta(seconds=60)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 5
SOURCE_TIME_ZONE = "Europe/Berlin"

PLATFORMS = ["sensor", "binary_sensor", "button"]
