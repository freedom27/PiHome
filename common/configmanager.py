import configparser
import os

config = configparser.ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__)) + '/pihome.ini')
