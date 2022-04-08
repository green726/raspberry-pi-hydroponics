from atlas_i2c import atlas_i2c
from time import sleep
from picamera import PiCamera, Color
from Adafruit_IO import Client, Feed
import base64
import requests
import json

cam = PiCamera()

mins = -1
# autoPump = True
phSens = atlas_i2c.AtlasI2C()
phSens.set_i2c_address(99)
ecSens = atlas_i2c.AtlasI2C()
ecSens.set_i2c_address(100)
temSens = atlas_i2c.AtlasI2C()
temSens.set_i2c_address(102)
humidSens = atlas_i2c.AtlasI2C()
humidSens.set_i2c_address(111)
pump = atlas_i2c.AtlasI2C()
pump.set_i2c_address(103)

username = "account"
key = "key"
aio = Client(username, key)
# pump.write("I2C,11")

phOut = aio.feeds('other1.ph')
pumpAmountAda = aio.feeds('other1.pumpamount')
airTempCOut = aio.feeds('other1.airtempcelcius')
airTempFOut = aio.feeds('other1.airtempfar')
autoPumpAda = aio.feeds('other1.auto-pump')
waterLevelBool = aio.feeds('other1.waterlevelbool')
waterTempCel = aio.feeds('other1.watertempcel')
waterTempFar = aio.feeds('other1.watertempfar')
cameraOut = aio.feeds('other1.camera')
ecOut = aio.feeds('other1.ec')
humidOut = aio.feeds('other1.humidity')
pumpButton = aio.feeds('other1.pumpbutton')


def send(feed, data):
    url = 'https://io.adafruit.com/api/v2/' + username + '/feeds/' + str(
        feed) + '/data'

    body = {'value': data}
    headers = {'X-AIO-Key': key, 'Content-Type': 'application/json'}
    try:
        r = requests.post(url, json=body, headers=headers)


#         print(r.text)
    except Exception as e:
        print("Send Error:", e)


def get(feed):
    url = 'https://io.adafruit.com/api/v2/' + username + '/feeds/' + str(
        feed) + '/data'

    headers = {'X-AIO-Key': key, 'Content-Type': 'application/json'}
    try:
        r = json.loads(requests.get(url, headers=headers).text)
        #         print(feed, r)
        return r[0]
    except Exception as e:
        print("Get Error:", e)


print(get("plantcoders.ec"))

# print("test")


def getHumidSens():
    humidSens.query("O,T,1", processing_delay=1500)
    humidSens.query("O,Dew,1", processing_delay=1500)
    humidLis = humidSens.query("R", processing_delay=1500)
    humidLis = humidLis.data.decode("utf-8").split(",")
    humidLis.append(humidLis[1])
    humidLis[4] = float(humidLis[4])
    humidLis[4] = humidLis[4] * 9 / 5 + 32
    humidLis[4] = str(humidLis[4])
    return humidLis


def getTemp():
    temReadC = temSens.query("R", processing_delay=1000)
    temReadC = temReadC.data.decode("utf-8")
    temReadF = float(temReadC)
    temReadF = temReadF * 9 / 5 + 32
    temReadF = str(temReadF)
    return temReadC, temReadF


def getPH():
    phRead = phSens.query("R", processing_delay=1000)
    phRead = phRead.data.decode("utf-8")
    return phRead


def getEC():
    ecRead = ecSens.query("R", processing_delay=1000)
    ecRead = ecRead.data.decode("utf-8")
    ecRead = float(ecRead)
    ecRead = ecRead / 1000
    ecRead = str(ecRead)
    return ecRead


def takePic():
    global pics
    pics = 0
    cam.resolution = (200, 200)
    cam.capture(
        "/home/pistudent-06/Documents/summer research 21/images/image.jpg")
    pics = pics + 1
    print("pics taken")
    sleep(.1)
    with open(
            "/home/pistudent-06/Documents/summer research 21/images/image.jpg",
            "rb") as imageFile:
        image = base64.b64encode(imageFile.read())
        sendStr = image.decode("utf-8")
        try:
            send(cameraOut.key, sendStr)
            print("Success")
        except:
            print("image send failed")


while True:
    try:
        pumpAmount = get(autoPumpAda.key)['value']
    except:
        print("rate limited... sleeping for 60")
        sleep(2)
    takePic()
    if get(pumpButton.key)['value'] == "ON":
        pump.write("D,40")
        send(pumpButton.key, "OFF")
#     pumpAmount = get(pumpAmountAda.key).value
    autoPump = get(autoPumpAda.key)['value']
    print(autoPump)
    print(pumpAmount)
    #     pump.write("x")
    phReading = getPH()
    print("ph:", phReading)
    send(phOut.key, phReading)
    ecReading = getEC()
    print("ec:", ecReading)
    send(ecOut.key, ecReading)
    if float(ecReading) < .2:
        print("EC is less than 1... water level may be low")
        send(waterLevelBool.key, 0)
        if autoPump == "ON":
            pump.write("D,100")
            autoPump = "OFF"
            while float(getEC()) < 1:
                pump.write("D,10")
    else:
        send(waterLevelBool.key, 1)
    tempList = getTemp()
    print("temp C:", tempList[0])
    print("temp F:", tempList[1])
    send(waterTempCel.key, tempList[0])
    send(waterTempFar.key, tempList[1])
    humidList = getHumidSens()
    print("Humid:", humidList[0])
    print("Air Temp C:", humidList[1])
    print("Air Temp F:", humidList[4])
    print("Dew Point:", humidList[3])
    send(humidOut.key, humidList[0])
    send(airTempCOut.key, humidList[1])
    send(airTempFOut.key, humidList[4])
    mins = mins + 1
    if mins == 10:
        takePic()
        mins = 0
    sleep(60)
