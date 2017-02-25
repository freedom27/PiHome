import RPi.GPIO as GPIO
from . import configmanager


if configmanager.config['gpio']['mode'] == "BCM":
    #logger.info("GPIO mode: BCM")
    GPIO.setmode(GPIO.BCM)
else:
    #logger.info("GPIO mode: BOARD")
    GPIO.setmode(GPIO.BOARD)
