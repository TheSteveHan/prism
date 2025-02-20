import json
import requests
import base64
import os

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ANALYTICS_SERVER = os.getenv(
    "ANALYTICS_SERVER",
    "localhost:5000"
)

def log_event(session_id, event_category, event_metadata):
  payload = {
      's': session_id,
      'c': event_category,
      'd': base64.b64encode(json.dumps(event_metadata).encode('utf-8')).decode('utf-8')
  }
  logger.debug(f"logging event {payload}")
  try:
      res= requests.post(f"http://{ANALYTICS_SERVER}/api/analytics/evt", json=payload)
      if not res.ok:
          logger.error(f"Failed to log event: {res.status_code}")
      else:
          logger.debug("Logged event")
  except Exception as e:
      logger.exception(e)

def log_assignment(result_id_type, result_id, exp_id, variant_id):
  payload = {
      result_id_type: result_id,
      'e': exp_id,
      'v': variant_id
  }
  logger.debug(f"logging assignment {payload}")
  try:
      res = requests.post(f"http://{ANALYTICS_SERVER}/api/analytics/exp", json=payload)
      if not res.ok:
          logger.error(f"Failed to log event: {res.status_code}")
      else:
          logger.debug("Logged assignment")
  except Exception as e:
      logger.exception(e)
