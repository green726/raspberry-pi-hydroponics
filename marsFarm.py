from atlas_i2c import atlas_i2c
from time import sleep
from picamera import PiCamera, Color
from Adafruit_IO import Client, Feed
import base64
# ph down 106, ph up 103

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
pump.set_i2c_address(104)
pump2 = atlas_i2c.AtlasI2C()
pump2.set_i2c_address(105)

aio = Client("CS_CSH","aio_ZqdK70vqX2K4b5JrDHm6ToaZ8Y0Y")

# pump.write("I2C,11")

phOut = aio.feeds('plantcoders.ph')
pumpAmountAda = aio.feeds('plantcoders.pumpamount')
airTempCOut = aio.feeds('plantcoders.airtempcelcius')
airTempFOut = aio.feeds('plantcoders.airtempfar')
autoPumpAda = aio.feeds('plantcoders.auto-pump')
waterLevelBool = aio.feeds('plantcoders.waterlevelbool')
waterTempCel = aio.feeds('plantcoders.watertempcel')
waterTempFar = aio.feeds('plantcoders.watertempfar')
cameraOut = aio.feeds('plantcoders.camera')
ecOut = aio.feeds('plantcoders.ec')
humidOut = aio.feeds('plantcoders.humidity')
pumpButton = aio.feeds('plantcoders.pumpbutton')
pumpButton2 = aio.feeds('plantcoders.pumpbuttontwo')
pumpAmountAda2 = aio.feeds('plantcoders.pumpamounttwo')

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
        humidLis = humidLis.data.decode("utf-8").split(",")
        humidLis.append(humidLis[1])
        humidLis[4] = float(humidLis[4])
        humidLis[4] = humidLis[4] * 9/5 + 32
        humidLis[4] = str(humidLis[4])
        return humidLis    
    except:
        print("Humidity Reading Failed")

def getTemp():
    try:
        temReadC = temSens.query("R", processing_delay = 1000)
        temReadC = temReadC.data.decode("utf-8")
        temReadF = float(temReadC)
        temReadF = temReadF  * 9/5 + 32
        temReadF = str(temReadF)
        return temReadC, temReadF
    except:
        print("Temperature Redng Failed")

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
        ecRead = float(ecRead)
        ecRead = ecRead / 1000
        ecRead = str(ecRead)
        return ecRead
    except:
        print("EC Reading Failed")

def takePic():
    try:
        global pics
        pics = 0
        cam.resolution = (280, 200)
        cam.capture("/home/pistudent-03/Documents/image.jpg")
        pics = pics + 1
        print("pics taken")
        sleep(.1)
        with open("/home/pistudent-03/Documents/image.jpg", "rb") as imageFile:
            image = base64.b64encode(imageFile.read())
            sendStr = image.decode("utf-8")
            send(cameraOut.key, sendStr)    
    except:
        print("Failed to take picture")
    
while True:
    try:
        pumpAmount = get(autoPumpAda.key).value
        takePic()
        sleep(5)
        
        pumpAmount = get(pumpAmountAda.key).value
        pumpAmount2 = get(pumpAmountAda2.key).value
        print(pumpAmount2)
        if get(pumpButton.key).value == "ON":
            pump.write("D," + pumpAmount)
            send(pumpButton.key, "OFF")
        if get(pumpButton2.key).value == "ON":
            pump2.write("D," + pumpAmount2)
            send(pumpButton2.key, "OFF")
        autoPump = aio.receive(autoPumpAda.key).value
        
        phReading = getPH()
        print("ph:", phReading)
        send(phOut.key, phReading)
        ecReading = getEC()
        print("ec:", ecReading)
        send(ecOut.key, ecReading)
        tempList  = getTemp()
        print("temp C:", tempList [0])
        print("temp F:", tempList[1])
        send(waterTempCel.key, tempList[0])
        send(waterTempFar.key, tempList[1])
        humidList = getHumidSens()
        try:
            print("Humid:", humidList[0])
            print("Air Temp C:", humidList[1])
            print("Air Temp F:", humidList[4])
            print("Dew Point:", humidList[3])
        except:
            print("humid list error")
        try:
            send(humidOut.key, humidList[0])
            send(airTempCOut.key, humidList[1])
            send(airTempFOut.key, humidList[4])
        except:
            print("humid list problem")
        mins = mins + 1
        if mins == 30:
            takePic()
            mins = 0
        sleep(60)
    except:
        print("Loop error")
