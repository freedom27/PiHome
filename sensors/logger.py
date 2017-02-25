import logging
import logging.config
import yaml


with open("sensors_logging.yml", "r") as config_file:
    logging.config.dictConfig(yaml.load(config_file))

logger = logging.getLogger('sensorsLogger')
