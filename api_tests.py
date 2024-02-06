import requests
import json
import datetime
import sqlite3
from bs4 import BeautifulSoup


# https://amendsonline.directline.com/motor/yourdetails

#                            Get number Data
#
# Just hit http://numbersapi.com/number/type to get a plain text response, where
#
#    type is one of trivia, math, date, or year. Defaults to trivia if omitted.
#    number is an integer, or the keyword random, for which we will try to return a random available fact, or
#    a day of year in the form month/day (eg. 2/29, 1/09, 04/1), if type is date
#    ranges of numbers
def get_number_data(month, day):
    url = "http://numbersapi.com/random/year"
    url = "http://numbersapi.com/" + str(month) + "/" + str(day) + "/date"
    response = requests.request("GET", url)
    return response.text


#                    Utility Convert Fahrenheit to Celsius
#   simple utility function to convert temperatures for NASA API calls.
def F_to_C(degrees):
    return ((degrees - 32) * 5) / 9


#                  NASA's Mars mission weather data.
#   this function will retrieve the current weather data in the corresponding Mars Sol.
#   it returns the sol number, average, min and max temperature and pressure on Mars.
def get_NASA(): # Not working. :(
    # temperatures are in degrees Celsius and pressure in Pa
    #
    url = "https://api.nasa.gov/insight_weather/?api_key=nJ27pQO5ajeWwVS2X72RWZa8r9qMIzSYeNrOiUcD&feedtype=json&ver=1.0"
    response = requests.get(url)
    # print(response.text)
    data = json.loads(response.content)
    # print(data['sol_keys'][6])
    # print(data[data['sol_keys'][6]]['AT']['av'])

    ret_val = {
        "sol": data['sol_keys'][6],
        "av_temp": F_to_C(data[data['sol_keys'][6]]['AT']['av']),
        "min_temp": F_to_C(data[data['sol_keys'][6]]['AT']['mn']),
        "max_temp": F_to_C(data[data['sol_keys'][6]]['AT']['mx']),
        "av_pres": data[data['sol_keys'][6]]['PRE']['av'],
        "min_pres": data[data['sol_keys'][6]]['PRE']['mn'],
        "max_pres": data[data['sol_keys'][6]]['PRE']['mx']}
    return ret_val


#              get XKCD comic strip from the day.
#   This function will get the daily XKCD comic strip and save it to the disk in the local /images folder
#   it will retain the name of the file as i kept on the website.
def get_xkcd():
    # http://xkcd.com/info.0.json
    image_path = "./images/"
    # get date for making up the url.
    date_now = datetime.datetime.now()
    url = "http://xkcd.com/info.0.json"
    response = requests.request("GET", url)
    data = json.loads(response.content)
    print(data['alt'])
    pic_address = data['img']
    r = requests.get(pic_address)
    temp = pic_address.split("/")
    pos = len(temp)
    file_name = temp[pos - 1]
    path = image_path + file_name

    # save comic file to disk.
    with open(path, 'wb') as f:
        f.write(r.content)
    f.close()


#             get Daily Dilbert comic strip
#   this function will download Dilbert's daily comic strip and name it with the current date of the day
#   the files do not have a readable name in the server, so this is a better approach.
def get_dilbert():
    image_path = "./images/"

    # get date for making up the url.
    date_now = datetime.datetime.now()
    # create daily url to understand where to get the image url from.
    url = "https://dilbert.com/strip/" + str(date_now.year) + "-" + str(date_now.month) + "-" + str(date_now.day)
    # get the html for the day.
    response = requests.request("GET", url)
    # parse the response
    soup = BeautifulSoup(response.text, 'html.parser')

    # find the correct property we want.
    res = soup.find(property="og:image")

    pic_address = res['content']  # content variable is the real image link.

    # request the image from the server.
    r = requests.get(pic_address)
    # create the file name for the file to be kept in the computer.
    file_name = str(date_now.year) + "-" + str(date_now.month) + "-" + str(date_now.day) + ".gif"
    path = image_path + file_name

    # save comic file to disk.
    with open(path, 'wb') as f:
        f.write(r.content)
    f.close()


#             Get ISS current position
#   this will return the current coordinates of the ISS probe circling the globe.
#   data is updated each second on NASA's servers
def get_ISS_position():
    # http://api.open-notify.org/iss-now.json
    url = "http://api.open-notify.org/iss-now.json"
    response = requests.get(url)
    # print(response.text)
    data = json.loads(response.content)
    ret_val = {"latitude": data['iss_position']['latitude'],
               "longitude": data['iss_position']['longitude']}
    return ret_val


#                 Get number and names of ISS astronauts
#   This will return a list with the names and number of astronauts currently at the ISS.
def get_ISS_astronauts():
    # http://api.open-notify.org/astros.json
    url = "http://api.open-notify.org/astros.json"
    response = requests.get(url)
    data = json.loads(response.content)
    ret_val = {"number": data['number'], "people": data['people']}
    return ret_val


#               Get the next time the ISS will be above the 10 degree radius above a certain geo location
#   This will return the start time and end time when the ISS crosses through the 1' degree radius above us.
def get_ISS_pass_time(_lat, _long):
    # casa 52.097079, 0.123908
    # synthomer 51.784511, 0.119237
    url = "http://api.open-notify.org/iss-pass.json?lat=" + str(_lat) + "&lon=" + str(_long)
    response = requests.get(url)
    data = json.loads(response.content)
    # print(data)
    start = data['response'][0]['risetime']
    end = start + data['response'][0]['duration']
    dt_start = datetime.datetime.fromtimestamp(start)  # this prints the correct time.
    dt_end = datetime.datetime.fromtimestamp(end)
    # time above the 10 degree circumference from location
    ret_val = {"start": dt_start, "end": dt_end}
    return ret_val


#   Get the energy mix currently being supplied to a given post code.
#   this will connect to the National Grid's servers and downloads the energy mix being supplied on a given post code
#   very interesting!!!!
def get_postcode_energy(_post):
    url = "https://api.carbonintensity.org.uk/regional/postcode/" + _post
    response = requests.get(url)
    # print(response.text)
    data = json.loads(response.content)
    now = datetime.datetime.now()
    ret_val = (now.strftime("%Y-%m-%d"),
               data['data'][0]['data'][0]['generationmix'][0]['perc'],
               data['data'][0]['data'][0]['generationmix'][1]['perc'],
               data['data'][0]['data'][0]['generationmix'][2]['perc'],
               data['data'][0]['data'][0]['generationmix'][3]['perc'],
               data['data'][0]['data'][0]['generationmix'][4]['perc'],
               data['data'][0]['data'][0]['generationmix'][5]['perc'],
               data['data'][0]['data'][0]['generationmix'][6]['perc'],
               data['data'][0]['data'][0]['generationmix'][7]['perc'],
               data['data'][0]['data'][0]['generationmix'][8]['perc'],)
    insert_into_db('tblEnergy', ret_val)
    ret_value = {
        data['data'][0]['data'][0]['generationmix'][0]['fuel']:
            data['data'][0]['data'][0]['generationmix'][0]['perc'],
        data['data'][0]['data'][0]['generationmix'][1]['fuel']:
            data['data'][0]['data'][0]['generationmix'][1]['perc'],
        data['data'][0]['data'][0]['generationmix'][2]['fuel']:
            data['data'][0]['data'][0]['generationmix'][2]['perc'],
        data['data'][0]['data'][0]['generationmix'][3]['fuel']:
            data['data'][0]['data'][0]['generationmix'][3]['perc'],
        data['data'][0]['data'][0]['generationmix'][4]['fuel']:
            data['data'][0]['data'][0]['generationmix'][4]['perc'],
        data['data'][0]['data'][0]['generationmix'][5]['fuel']:
            data['data'][0]['data'][0]['generationmix'][5]['perc'],
        data['data'][0]['data'][0]['generationmix'][6]['fuel']:
            data['data'][0]['data'][0]['generationmix'][6]['perc'],
        data['data'][0]['data'][0]['generationmix'][7]['fuel']:
            data['data'][0]['data'][0]['generationmix'][7]['perc'],
        data['data'][0]['data'][0]['generationmix'][8]['fuel']:
            data['data'][0]['data'][0]['generationmix'][8]['perc'],
    }
    return ret_value


def get_weather(location_id):
    base_address = "http://api.openweathermap.org/data/2.5/weather?id="
    weather_key = "d087e1939ad1670b69f653f3737ab2d8"
    location_dict = {
        "Harlow": "2647461",
        "Duxford": "2650605",
        "London": "2643743",
        "Rio Tinto": "8012715",
        "Armacao": "8014395",
        "Porto": "6458924"
    }
    url = base_address + location_dict[location_id] + "&units=metric&appid=" + weather_key
    response = requests.get(url)
    data = json.loads(response.content)
    now = datetime.datetime.now()
    date_time = now.strftime("%Y/%m/%d %H:%M:%S")
    ret_val = (date_time, data['name'], data['main']['temp'],data['main']['pressure'],data['main']['humidity'],data['wind']['speed'],)
    insert_into_db('tblWeather', ret_val)
    return ret_val


def get_bin_collection():

    #There are 3 types of collections: ORGANIC (green), DOMESTIC (black) and RECYCLE (blue).
    # url = "https://www.scambs.gov.uk/bins/find-your-household-bin-collection-day/#id=10003874796"

    url = "https://servicelayer3c.azure-api.net/wastecalendar/collection/search/10003874796/?numberOfCollections=1"

    # get the html for the day.
    response = requests.request("GET", url)
    data = json.loads(response.content)

    # recycling, domestic, organic (green, blue, black)
    dia = data["collections"][0]["date"].split('T')

    ret_val = (dia[0], data["collections"][0]["roundTypes"][0])

    if len(data["collections"][0]["roundTypes"]) == 2:
        # There are two collections on that day
        ret_val +=(data["collections"][0]["roundTypes"][1],)
    else:
        ret_val += (" ",)

    # print(data["collections"][0]["date"])
    # print(data["collections"][0]["roundTypes"])
    # print(len(data["collections"][0]["roundTypes"]))
    #print(len(data["collections"][0]["roundTypes"]))
    print (ret_val)
    insert_into_db('tblBinCollection', ret_val)

def get_pollen(county):
    counties_dict = {
        "Orkney and Shetland": "os",
        "Central, Tayside and Fife": "ta",
        "Highlands &Eileen Siar": "he",
        "Grampian": "gr",
        "Strathclyde": "st",
        "Dumfries, Galloway, Lothian and Borders": "dg",
        "Northern Ireland": "ni",
        "Wales": "wl",
        "North West England": "nw",
        "North East England": "ne",
        "Yorkshire and Humber": "yh",
        "West Midlands": "wm",
        "East Midlands": "em",
        "East of England": "ee",
        "South West England": "sw",
        "London and South East": "se"
    }
    data = datetime.date.today()
    url = "https://www.metoffice.gov.uk/weather/warnings-and-advice/seasonal-advice/pollen-forecast#?date=" + data.strftime(
        '%Y-%m-%d')

    response = requests.request("GET", url)

    # parse the response
    soup = BeautifulSoup(response.text, 'html.parser')
    print (soup)
    bowl = soup.find("div", {"id": counties_dict[county]})

    # This will return the pollen forecast for today... however it picks up the first result. We want ee.
    pollen_today = bowl.find("span", {"class": "icon", "data-type": "pollen", "title": True})['title']
    pollen_description = bowl.p.get_text()
    print(pollen_today)
    print(pollen_description)
    ret_val = (data.strftime('%Y-%m-%d'), pollen_today, pollen_description)
    insert_into_db('tblPollen', ret_val)


#            Downloads a random advice from a website.
#   returns a simple text string with an advice.
def get_advice():
    url = "https://api.adviceslip.com/advice"
    response = requests.get(url)
    # print(response.text)
    data = json.loads(response.content)
    # print(data)

    now = datetime.datetime.now()
    date_time = now.strftime("%m/%d/%Y")

    ret_val = (date_time, data['slip']['advice'],)

    insert_into_db('tblAdvice', ret_val)
    return ret_val


#               Get current exchange rate to dollar and euro from GBP
#   returns the current exchange rates for the two main currencies against the GBP.
def get_forex():
    # GET https://api.exchangeratesapi.io/latest?base=USD HTTP/1.1
    url = "https://api.exchangeratesapi.io/latest?base=GBP"
    response = requests.get(url)
    # print(response.text)
    data = json.loads(response.content)
    ret_val = (data['date'], data['base'],data['rates']['USD'],data['rates']['EUR'],)
    insert_into_db('tblForex', ret_val)
    return ret_val


def insert_into_db(table, dados):

    # Prepare query to be run
    query = 'INSERT INTO ' + table + ' VALUES ('
    # the for below is to compose the string to add the data to the Database as we may add any number of columns
    for x in range(len(dados)-1):
        query += '?,'
    query+= '?)' # this is the last element, hence why we run the loop to -1

    # connect to the database
    try:
        conn = sqlite3.connect('assistantData.db')
        c = conn.cursor()
        # execute query
        c.execute(query,  dados)
        # save changes
        conn.commit()
        # exit
        conn.close()
    except sqlite3.IntegrityError:
        return -1
    except sqlite3.OperationalError:
        return -2

now = datetime.datetime.now()
data = datetime.date.today()

def send_email():
    import smtplib
    from email.mime.text import MIMEText

    password = '34Pepperslade'
    username = 'pepperslade@sapo.pt'

    smtp_ssl_host = 'smtp.sapo.pt'
    smtp_ssl_port = 465

    from_addr = 'pepperslade@sapo.pt'
    to_addrs = ['bubulindo@gmail.com']

    message = MIMEText('Hello World')
    message['subject'] = 'Hello'
    message['from'] = from_addr
    message['to'] = ', '.join(to_addrs)

    server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)

    server.login(username, password)
    server.sendmail(from_addr, to_addrs, message.as_string())
    server.quit()

def receive_email():
    import email
    import imaplib

    EMAIL = 'pepperslade@sapo.pt'
    PASSWORD = '34Pepperslade'
    SERVER = 'imap.sapo.pt'

    # connect to the server and go to its inbox
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)
    # we choose the inbox but you can select others
    mail.select('inbox') #inbox

    # we'll search using the ALL criteria to retrieve
    # every message inside the inbox
    # it will return with its status and a list of ids
    status, data = mail.search(None, 'ALL')
    # the list returned is a list of bytes separated
    # by white spaces on this format: [b'1 2 3', b'4 5 6']
    # so, to separate it first we create an empty list
    mail_ids = []
    # then we go through the list splitting its blocks
    # of bytes and appending to the mail_ids list
    for block in data:
        # the split function called without parameter
        # transforms the text or bytes into a list using
        # as separator the white spaces:
        # b'1 2 3'.split() => [b'1', b'2', b'3']
        mail_ids += block.split()

    # now for every id we'll fetch the email
    # to extract its content
    for i in mail_ids:
        # the fetch function fetch the email given its id
        # and format that you want the message to be
        status, data = mail.fetch(i, '(RFC822)')

        # the content data at the '(RFC822)' format comes on
        # a list with a tuple with header, content, and the closing
        # byte b')'
        for response_part in data:
            # so if its a tuple...
            if isinstance(response_part, tuple):
                # we go for the content at its second element
                # skipping the header at the first and the closing
                # at the third
                message = email.message_from_bytes(response_part[1])

                # with the content we can extract the info about
                # who sent the message and its subject
                mail_from = message['from']
                mail_subject = message['subject']

                # then for the text we have a little more work to do
                # because it can be in plain text or multipart
                # if its not plain text we need to separate the message
                # from its annexes to get the text
                if message.is_multipart():
                    mail_content = ''

                    # on multipart we have the text message and
                    # another things like annex, and html version
                    # of the message, in that case we loop through
                    # the email payload
                    for part in message.get_payload():
                        # if the content type is text/plain
                        # we extract it
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    # if the message isn't multipart, just extract it
                    mail_content = message.get_payload()

                # and then let's show its result
                print(f'From: {mail_from}')
                print(f'Subject: {mail_subject}')
                print(f'Content: {mail_content}')

# print(get_number_data(now.month, now.day))

# print(get_NASA())
# get_dilbert()
# get_xkcd()
# print(get_forex())
print(get_advice())
print(get_ISS_position())
print(get_ISS_astronauts())
# print(get_ISS_pass_time(52.097079, 0.123908))
# print(get_weather("Harlow"))
print(get_weather("Duxford"))
get_bin_collection()
# get_pollen("East of England")
print(get_postcode_energy('CB22'))

# res = get_postcode_energy('CB22')
# print(res['nuclear'])
# send_email()
# receive_email()
# res = get_weather("Duxford")
# print(res[2])