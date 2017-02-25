import os
import logging
import logging.config
import yaml


with open(os.path.dirname(os.path.abspath(__file__)) + "/sensors_logging.yml", "r") as config_file:
    logging.config.dictConfig(yaml.load(config_file))

logger = logging.getLogger('sensorsLogger')
