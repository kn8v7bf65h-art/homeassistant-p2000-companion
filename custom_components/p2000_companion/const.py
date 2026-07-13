"""Constants for P2000 Companion."""

DOMAIN = "p2000_companion"

DEFAULT_NAME = "P2000 Monitor"
DEFAULT_FEED_URL = "https://alarmeringen.nl/feeds/region/haaglanden.rss"
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_CREATE_FEED_SENSOR = False

CONF_MONITOR_NAME = "monitor_name"
CONF_FEED_URL = "feed_url"
CONF_CITIES = "cities"
CONF_SERVICES = "services"
CONF_PRIORITIES = "priorities"
CONF_EXCLUDE_WORDS = "exclude_words"
CONF_TEXT_CONTAINS = "text_contains"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CREATE_FEED_SENSOR = "create_feed_sensor"

EVENT_FEED_ALERT = "p2000_feed_alert"
EVENT_FILTERED_ALERT = "p2000_filtered_alert"
EVENT_LEGACY_FILTERED_ALERT = "p2000_new_alert"
EVENT_MONITOR_PREFIX = "p2000_monitor_"

PLATFORMS = ["sensor"]

SERVICE_OPTIONS = ["ambulance", "fire", "police", "mmt", "lifeboat"]
PRIORITY_OPTIONS = ["P1", "P2", "P3", "B1", "B2"]
