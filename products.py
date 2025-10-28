# Product modules, add new ones here as needed.
from forecast import getForecast
from alert_summary import getAlertSummary
from hazardous_weather_outlook import getHazardousWeatherOutlook
from tropical_weather_outlook import getTropicalWeatherOutlook
from current_time import getCurrentTime
from area_observations import getObservations

PRODUCT_GENERATORS = (
    getAlertSummary,
    getForecast,
    getObservations,
    getHazardousWeatherOutlook,
    getTropicalWeatherOutlook,
    getCurrentTime,
)
