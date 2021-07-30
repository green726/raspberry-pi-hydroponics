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
pump3 = atlas_i2c.AtlasI2C()
pump3.set_i2c_address(106)
pump4 = atlas_i2c.AtlasI2C()
pump4.set_i2c_address(103)

username = "CS_CSH"
key = "aio_ZqdK70vqX2K4b5JrDHm6ToaZ8Y0Y"
aio = Client(username,key)

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
pumpButton3 = aio.feeds('plantcoders.pumpbutton3')
pumpButton4 = aio.feeds('plantcoders.pumpbutton4')
pumpAmountAda3 = aio.feeds('plantcoders.pumpamountthree')
pumpAmountAda4 = aio.feeds('plantcoders.pumpamountfour')

def getHumidSens():
    humidSens.query("O,T,1", processing_delay = 1500)
    humidSens.query("O,Dew,1", processing_delay = 1500)
    sleep(1.5)
    humidLis = humidSens.query("R", processing_delay = 1500)
    try:
        humidLis = humidLis.data.decode("utf-8").split(",")
        humidLis[4] = float(humidLis[4])
        humidLis[4] = humidLis[4] * 9/5 + 32
        humidLis[4] = str(humidLis[4])
        return humidLis
    except:
        print("utf-8 decode error")
    try:
        humidLis.append(humidLis[1])
    except:
        print("humid list error")
   

def getTemp():
    temReadC = temSens.query("R", processing_delay = 1000)
    temReadC = temReadC.data.decode("utf-8")
    temReadF = float(temReadC)
    temReadF = temReadF  * 9/5 + 32
    temReadF = str(temReadF)
    return temReadC, temReadF

def getPH():
    phRead = phSens.query("R", processing_delay = 1000)
    phRead = phRead.data.decode("utf-8")
    return phRead
    
def getEC():
    ecRead = ecSens.query("R", processing_delay = 1000)
    ecRead = ecRead.data.decode("utf-8")
    ecRead = float(ecRead)
    ecRead = ecRead / 1000
    ecRead = str(ecRead)
    return ecRead

def takePic():
    global pics
    pics = 0
    cam.resolution = (280, 200)
    cam.capture("/home/pistudent-21/Documents/summer research 21/gardenImages/image.jpg")
    pics = pics + 1
    print("pics taken")
    sleep(.1)
    with open("/home/pistudent-21/Documents/summer research 21/gardenImages/image.jpg", "rb") as imageFile:
        image = base64.b64encode(imageFile.read())
        sendStr = image.decode("utf-8")
        try:
            aio.send(cameraOut.key, sendStr)
        except:
            print("image send failed")

while True:
#     pump2.write("D," + "-2")
    try:
        pumpAmount = aio.receive(autoPumpAda.key).value
    except:
        sleep(60)
    takePic()
    sleep(5)
    
    pumpAmount = aio.receive(pumpAmountAda.key).value
    pumpAmount2 = aio.receive(pumpAmountAda2.key).value
    pumpAmount3 = aio.receive(pumpAmountAda3.key).value
    pumpAmount4 = aio.receive(pumpAmountAda4.key).value
    print(pumpAmount2)
    if aio.receive(pumpButton.key).value == "ON":
        pump.write("D," + pumpAmount)
        aio.send(pumpButton.key, "OFF")
    if aio.receive(pumpButton2.key).value == "ON":
        print("test")
        pump2.write("D," + pumpAmount2)
        aio.send(pumpButton2.key, "OFF")
#     pumpAmount = aio.receive(pumpAmountAda.key).value
    if aio.receive(pumpButton3.key).value == "ON":
        print("test3 " + pumpAmount4)
        pump3.write("D," + pumpAmount3)
        aio.send(pumpButton3.key, "OFF")
    if aio.receive(pumpButton4.key).value == "ON":
        print("test4 " + pumpAmount4)
        pump4.write("D," + pumpAmount4)
        aio.send(pumpButton4.key, "OFF")
    autoPump = aio.receive(autoPumpAda.key).value
    print(autoPump)
#     pump.write("x")   
    phReading = getPH()
    print("ph:", phReading)
    aio.send(phOut.key, phReading)
    ecReading = getEC()
    print("ec:", ecReading)
    aio.send(ecOut.key, ecReading)
    if float(ecReading) < .2:
        print("EC is less than 1... water level may be low")
        aio.send(waterLevelBool.key, 0)
        if autoPump == "ON":
            pump.write("D,100")
            autoPump = "OFF";
            while float(getEC()) < 1:
                pump.write("D,10")
    else:
        aio.send(waterLevelBool.key, 1)
    tempList  = getTemp()
    print("temp C:", tempList [0])
    print("temp F:", tempList[1])
    aio.send(waterTempCel.key, tempList[0])
    aio.send(waterTempFar.key, tempList[1])
    humidList = getHumidSens()
    try:
        print("Humid:", humidList[0])
        print("Air Temp C:", humidList[1])
        print("Air Temp F:", humidList[4])
        print("Dew Point:", humidList[3])
    except:
        print("humid list error")
    try:
        aio.send(humidOut.key, humidList[0])
        aio.send(airTempCOut.key, humidList[1])
        aio.send(airTempFOut.key, humidList[4])
    except:
        print("humid list problem")
    mins = mins + 1
    if mins == 30:
        takePic()
        mins = 0
    sleep(120)

   