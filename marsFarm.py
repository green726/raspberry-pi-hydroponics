auto = True
pi = '03'

loopTime = 10 # In mins
optimalRanges = {
    "ph": {"top": 6.2, "bottom": 5.4},
    "ec": {"top": 1.6, "bottom": .8}
}

addresses = {
    "phSense": 0x63,
    "ecSense": 0x64,
    "tempSense": 0x66,
    "humidSense": 0x6f,
    "nutrientsIn": 0x05,
    "waterIn": 0x06,
    "waterOut": 0x16,
    "phUp": 0x07,
    "phDown": 0x17
}

from atlas_i2c import atlas_i2c
from time import sleep, time
from picamera import PiCamera, Color
from Adafruit_IO import Client, Feed
from datetime import datetime, date
import base64
# ph down 106, ph up 103

# cam = PiCamera()

# Makes it take the first pic after 2.5mins 
mins = 25

# autoPump = True
phSens = atlas_i2c.AtlasI2C(addresses["phSense"])
ecSens = atlas_i2c.AtlasI2C(addresses["ecSense"])
temSens = atlas_i2c.AtlasI2C(addresses["tempSense"])
humidSens = atlas_i2c.AtlasI2C(addresses["humidSense"])

#Creates all of the pump vars and makes them None (python null)
nutrientsIn=waterIn=waterOut=phUp=phDown=None
lastpHDose=lastECDose=0

if auto:
    nutrientsIn = atlas_i2c.AtlasI2C(addresses["nutrientsIn"])
    waterIn = atlas_i2c.AtlasI2C(addresses["waterIn"])
    waterOut = atlas_i2c.AtlasI2C(addresses["waterOut"])
    phUp = atlas_i2c.AtlasI2C(addresses["phUp"])
    phDown = atlas_i2c.AtlasI2C(addresses["phDown"])


aio = Client("CS_CSH","aio_ZqdK70vqX2K4b5JrDHm6ToaZ8Y0Y")

# pump.write("I2C,11")

farm = pi == 21 and 'plantcoders' or 'other1'
phOut = aio.feeds(farm + '.ph')
pumpAmountAda = aio.feeds(farm + '.pumpamount')
airTempCOut = aio.feeds(farm + '.airtempcelcius')
airTempFOut = aio.feeds(farm + '.airtempfar')
autoPumpAda = aio.feeds(farm + '.auto-pump')
waterLevelBool = aio.feeds(farm + '.waterlevelbool')
waterTempCel = aio.feeds(farm + '.watertempcel')
waterTempFar = aio.feeds(farm + '.watertempfar')
cameraOut = aio.feeds(farm + '.camera')
ecOut = aio.feeds(farm + '.ec')
humidOut = aio.feeds(farm + '.humidity')
pumpButton = aio.feeds(farm + '.pumpbutton')
pumpButton2 = aio.feeds(farm + '.pumpbuttontwo')
pumpAmountAda2 = aio.feeds(farm + '.pumpamounttwo')

def send(feed, data):
    try:
        aio.send(feed, data)
    except:
        print("Failed to send data to feed:", str(feed))
        
def get(feed):
    try:
        return aio.receive(feed)
    except:
        print("Failed to get data from feed:", str(feed))

def getHumidSens():
    try:
        humidSens.query("O,T,1", processing_delay = 1500)
        humidSens.query("O,Dew,1", processing_delay = 1500)
        humidLis = humidSens.query("R", processing_delay = 1500)
        humList = humidLis.data.decode("utf-8").split(",")
        #0: Humidity, 1: airTempC, 3: Dew Point
        airTempF = float(humList[1]) * 9/5 + 32
        return humList[0], humList[1], airTempF, humList[3]
    except Exception as e:
        print("Humidity Reading Failed")
        print(e)

def getTemp():
    try:
        temReadC = temSens.query("R", processing_delay = 1000)
        temReadC = temReadC.data.decode("utf-8")
        temReadF = float(temReadC) * 9/5 + 32
        return temReadC, temReadF
    except Exptio:
        print("Temperature Reading Failed")

def getPH():
    try:
        phRead = phSens.query("R", processing_delay = 1000)
        phRead = phRead.data.decode("utf-8")
        return phRead
    except:
        print("PH Reading Failed")
        
def getEC():
    try:
        ecRead = ecSens.query("R", processing_delay = 1000)
        ecRead = ecRead.data.decode("utf-8")
        ecRead = float(ecRead) / 1000
        return ecRead
    except:
        print("EC Reading Failed")

def takePic():
    try:
        global pics
        pics = 0
        cam.resolution = (250, 200)
        cam.capture(f"/home/pistudent-{pi}/Documents/image.jpg")
        pics = pics + 1
        sleep(.1)
        with open(f"/home/pistudent-{pi}/Documents/image.jpg", "rb") as imageFile:
            image = base64.b64encode(imageFile.read())
            sendStr = image.decode("utf-8")
            send(cameraOut.key, sendStr)    
    except:
        print("Failed to take picture")
    
while True:
    try:
        phReading = getPH()
        print("ph:", phReading)
        send(phOut.key, phReading)
        
        ecReading = getEC()
        print("ec:", ecReading)
        send(ecOut.key, ecReading)    
        
        tempC, tempF = getTemp()
        print("temp C:", tempC)
        print("temp F:", tempF)
        send(waterTempCel.key, tempC)
        send(waterTempFar.key, tempF)
        
        humid, airTempC, airTempF, dewPoint = getHumidSens()
        print("Humid:", humid)
        
        print("Air Temp C:", airTempC)
        print("Air Temp F:", airTempF)
        print("Dew Point:", dewPoint)
        send(humidOut.key, humid)
        send(airTempCOut.key, airTempC)
        send(airTempFOut.key, airTempF)
            
#         mins = mins + 1
#         if mins == 30:
#             try:
#                 takePic()
#                 mins = 0
#                 print("Took picture")
#             except:
#                 print("Failed to take picture")
#                 mins = 25
        
        if auto:
            currentTime = time()
            
            currentTimeStr = datetime.now().strftime("%H:%M")
            currentDay = date.today()
            
            if float(phReading) > optimalRanges["ph"]["top"] and currentTime - lastpHDose >= loopTime * 60:
                print("pH Down " + str(currentDay) + " " + str(currentTimeStr))
                phDown.write("D,2")
                lastpHDose = currentTime
            elif float(phReading) < optimalRanges["ph"]["bottom"] and currentTime - lastpHDose >= loopTime * 60:
                print("pH Up " + str(currentDay) + " " + str(currentTimeStr))
                phUp.write("D,5")
                lastpHDose = currentTime
            if float(ecReading) > optimalRanges["ec"]["top"] and currentTime - lastECDose >= loopTime * 60:
                print("Ec Down " + str(currentDay) + " " + str(currentTimeStr))
                waterOut.write("D,-5")
                sleep(5)
                waterIn.write("D,5")
                lastECDose = currentTime
            elif float(ecReading) < optimalRanges["ec"]["bottom"] and currentTime - lastECDose >= loopTime * 60:
                print("Ec Up " + str(currentDay) + " " + str(currentTimeStr))
                nutrientsIn.write("D,5")
                lastECDose = currentTime
        sleep(10)
    except Exception as e:
        print("Loop failed with error: " + str(e))
        sleep(5)
 