#!/usr/bin/env python3
import sqlite3
import sys 
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
print(picdir)
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')

if os.path.exists(libdir):
    sys.path.append(libdir)
    print("exists")

import logging
from waveshare_epd import epd2in7
import time
from PIL import Image, ImageDraw, ImageFont
import traceback
import RPi.GPIO as GPIO

logging.basicConfig(level=logging.DEBUG)

# Set up fonts.
font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
font18 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)
font35 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 35)
menuFont = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 25)
GPIO.setmode(GPIO.BCM)
# This is the assistant code for the RPi and e-paper.
# the purpose is to display a menu that will enable the functions to be called.
# The data will be refreshed onto a database daily.
# Advice, Bin collection, pollen, weather, Energy, Forex


# We want to pull the last row from each table.
def get_data_from_db(table):
    query = 'SELECT * FROM ' + table + ' ORDER BY Date DESC Limit 1'

    # connect to the database
    try:
        conn = sqlite3.connect('assistantData.db')
        c = conn.cursor()
        # execute query
        c.execute(query)
        rows = c.fetchone()

        return rows
        # exit
        conn.close()
    except sqlite3.IntegrityError:
        pass #return -1
    except sqlite3.OperationalError:
        pass#return -2


class eScreen:

    def clearScreen(self):
        self.Himage = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
        self.draw = ImageDraw.Draw(self.Himage)

    def printWeather(self):
        self.clearScreen() # clear whatever is there.
        result = get_data_from_db('tblWeather')
        # split result[0] on space to get the day
        string = str(result[2]) + " ºC\n" + str(result[3]) + " mbar\n" + str(result[4]) + " %\n" + str(result[5]) + " m/s"
        self.draw.text((10, 10), string, font=self.font, fill=0)
        self.epd.display(self.epd.getbuffer(self.Himage))
        print("Weather")

    def printAdvice(self):
        self.clearScreen() # clear whatever is there.
        res = get_data_from_db('tblAdvice')
        # print "res[1]" Need to account for new line...
        string = "coming soon!!"
        self.draw.text((10, 10), string, font=self.font, fill=0)
        self.epd.display(self.epd.getbuffer(self.Himage))

    def printForex(self):
        self.clearScreen() # clear whatever is there.
        res = get_data_from_db('tblForex')
        # 1 GBP =
        # res[2] "USD"
        # res[3] "EUR" # need to trim the decimal places off of the exchange rate.
        string = res[0] + "\n" + "1 GBP =\n" + str(round(res[2],2)) + " USD\n" + str(round(res[3],2)) + " EUR"
        self.draw.text((10, 10), string, font=self.font, fill=0)
        self.epd.display(self.epd.getbuffer(self.Himage))

    def printPollen(self):
        self.clearScreen() # clear whatever is there.
        res = get_data_from_db('tblPollen')
        # res[0] Data da previsão
        # res[1] previsão (very high, high, moderate, low, very low pollen)
        string = res[0] + "\n" + res[1]
        self.draw.text((10, 10), string, font=self.font, fill=0)
        self.epd.display(self.epd.getbuffer(self.Himage))

    def printBinCollection(self):
        self.clearScreen() # clear whatever is there.
        res = get_data_from_db('tblBinCollection')
        # res[0] - Date of the bin collection. Trim the string from the T onwards.
        # res[1] - first type.
        # res[2] - if not ' ', then print which will be the second type to bin collection.
        string = res[0] + "\n" + res[1] + "\n" + res[2]
        self.draw.text((10, 10), string, font=self.font, fill=0)
        self.epd.display(self.epd.getbuffer(self.Himage))

    def printEnergyMix(self):
        self.clearScreen() # clear whatever is there.
        res = get_data_from_db('tblEnergy')
        # there isn't space to print all of the generation types. so we'll focus on the main 4
        # res['gas']
        # res['nuclear']
        # res['solar']
        # res['wind']
        # split on space res['Date']
        # {1:'biomass': 11.9, 2:'coal': 0, 3:'imports': 0, 4:'gas': 34.1, 5:'nuclear': 16.9, 6:'other': 0, 7:'hydro': 0, 8:'solar': 23.4, 9:'wind': 13.7}
        string = res[0] + "\n" + "nuclear: " + str(res[5]) + " %\n" + "gas: " + str(res[4]) + " %\n" + "solar: " + str(res[8]) + " %\n" + "wind: " + str(res[9]) + " %"
        self.draw.text((10, 10), string, font=self.font, fill=0)
        self.epd.display(self.epd.getbuffer(self.Himage))
        
    # I've kept the fucntion that displays the data tied to the rest of the information for each of the data.
    # to call these functions, we instead call _options[information][2]()
    _options = [['Weather', 'tblWeather', printWeather],
                ['Pollen', 'tblPollen', printPollen],
                ['Bin Collection', 'tblBinCollection', printBinCollection],
                ['Forex', 'tblForex', printForex],
                ['Advice', 'tblAdvice', printAdvice],
                ['Energy Mix', 'tblEnergy', printEnergyMix]]

    _topOption = 0 # this is the pointer to the _options "array"
    _numOptions = 6 # the number of options to select.
    # Screen 99 is where the options to go in are displayed.
    # Weather will be screen 0
    # Pollen will be screen 1
    # essentially the screen number should tie in with the index in the _options menu.
    _currentScreen = 99
    # this is the number of buttons minus the return key. I could look at a timed change too...
    _screenOptions = 3

    def __init__(self):
        # initialize variables
        self.topOption = 0
        self._currentScreen = 99
        # initialise hardware
        GPIO.setmode(GPIO.BCM)
        self.key1 = 5
        self.key2 = 6
        self.key3 = 13
        self.key4 = 19

        try:
            logging.info("epd2in7 Demo")

            self.epd = epd2in7.EPD()

            '''2Gray(Black and white) display'''
            logging.info("init and Clear")
            self.epd.init()
            self.epd.Clear(0xFF)

            # Set up GPIO
            GPIO.setup(self.key1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.key2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.key3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.key4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            self.Himage = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
            self.draw = ImageDraw.Draw(self.Himage)
            self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
        except:
            pass

    def incrementPointer(self):
        self._topOption += 1
        if self._topOption > self._numOptions-1:
            self.topOption = 0
        

    def printMenu(self):
        self.clearScreen() # clear whatever is there.
        options = range(self._screenOptions)
        initialPosition = 10
        for n in options: # print all the options that fit in the space to terminal. Later to be moved to screen.
            string = self._options[(self._topOption + n) % self._numOptions][0]
            self.draw.text((10, initialPosition), string, font=menuFont, fill=0)
            initialPosition = initialPosition + 40
            
        self.epd.display(self.epd.getbuffer(self.Himage))
            
            # print(self._options[(self._topOption + n) % self._numOptions][0])

    def K1(self):
        self._currentScreen = self._topOption
        self._options[(self._topOption) % self._numOptions][2](self)   # this will call the display function tied to the index in the menu.
        
    def K2(self):
        self._currentScreen = self._topOption + 1
        self._options[(self._topOption + 1) % self._numOptions][2](self)  # this will call the display function tied to the index in the menu.

    def K3(self):
        self._currentScreen = self._topOption + 2
        self._options[(self._topOption + 2) % self._numOptions][2](self)  # this will call the display function tied to the index in the menu.

    def K4(self): # this will be tied to key K4
        if self._currentScreen != 99:
            self._currentScreen = 99
        else:
            self.incrementPointer()
        self.printMenu()
        
res = get_data_from_db('tblEnergy')
print(res)
# {'biomass': 11.9, 'coal': 0, 'imports': 0, 'gas': 34.1, 'nuclear': 16.9, 'other': 0, 'hydro': 0, 'solar': 23.4, 'wind': 13.7}

myScreen = eScreen()
myScreen.printMenu()

while True:
    key1state = GPIO.input(myScreen.key1)
    key2state = GPIO.input(myScreen.key2)
    key3state = GPIO.input(myScreen.key3)
    key4state = GPIO.input(myScreen.key4)
    
    if key1state == False:
        myScreen.K1()
        print("K1")
    if key2state == False:
        myScreen.K2()
        print("K2")
    if key3state == False:
        myScreen.K3()
        print("K3")
    if key4state == False:
        myScreen.K4()
        print("K4")


# print(myScreen._options[0][1])

# myScreen.K2()
# myScreen.incrementPointer()
# myScreen.incrementPointer()
# print("pointer")
# myScreen.printMenu()
# print("keys")
# myScreen.K1()
# myScreen.K2()
# myScreen.K3()