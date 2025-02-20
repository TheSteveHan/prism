import os
import requests
from growthbook import GrowthBook
from clients.analytics import log_assignment

GROWTH_BOOK_URL = os.getenv(
    'GROWTH_BOOK_URL',
    "http://localhost:4100/api/features/key_prod_28cb340aba52f675"
)

# Tracking callback when someone is put in an experiment
def on_experiment_viewed(experiment, result):

  # Use whatever event tracking system you want
  id_type_map = {
      'user_id': 'u',
      'session_id': 's'
  }
  result_id_type = id_type_map.get(result.hashAttribute, None)
  if not result_id_type:
      return
  result_id = result.hashValue
  log_assignment(
      result_id_type,
      result_id,
      experiment.key,
      result.variationId
  )


def get_feature_value(user, feature, default_value=None):
    # Fetch feature definitions from GrowthBook API
    # In production, we recommend adding a db or cache layer
    apiResp = requests.get(GROWTH_BOOK_URL)
    features = apiResp.json()["features"]
    # TODO: Real user attributes
    attributes = {
      "user_id": user.uuid.hex,
    }
    # Create a GrowthBook instance
    gb = GrowthBook(
      attributes = attributes,
      features = features,
      trackingCallback = on_experiment_viewed
    )

    value = gb.getFeatureValue(feature, default_value)
    gb.destroy()
    return value
