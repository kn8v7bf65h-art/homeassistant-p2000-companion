"""Constants for P2000 Companion."""

DOMAIN = "p2000_companion"

DEFAULT_NAME = "P2000 Companion"
DEFAULT_FEED_URL = "https://alarmeringen.nl/feeds/region/haaglanden.rss"
DEFAULT_SCAN_INTERVAL = 60

CONF_FEED_URL = "feed_url"
CONF_CITIES = "cities"
CONF_SERVICES = "services"
CONF_PRIORITIES = "priorities"
CONF_EXCLUDE_WORDS = "exclude_words"
CONF_SCAN_INTERVAL = "scan_interval"

EVENT_FEED_ALERT = "p2000_feed_alert"
EVENT_FILTERED_ALERT = "p2000_new_alert"

PLATFORMS = ["sensor"]

SERVICE_OPTIONS = ["ambulance", "brandweer", "politie", "traumaheli"]
PRIORITY_OPTIONS = ["P1", "P2", "P3", "A1", "A2", "B1"]
