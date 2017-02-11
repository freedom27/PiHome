import RPi.GPIO as GPIO
import configmanager


if configmanager.config['gpio']['mode'] == "BCM":
    GPIO.setmode(GPIO.BCM)
else:
    GPIO.setmode(GPIO.BOARD)
