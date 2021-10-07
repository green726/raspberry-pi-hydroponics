auto = False
pi = 21

from atlas_i2c import atlas_i2c
from time import sleep
from picamera import PiCamera, Color
from Adafruit_IO import Client, Feed
import base64
# ph down 106, ph up 103

cam = PiCamera()

# Makes it take the first pic after 2.5mins 
mins = 25

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
pump2 = atlas_i2c.AtlasI2C()
pump2.set_i2c_address(106)

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
        humid, airTempC, _, dewPoint = humidLis.data.decode("utf-8").split(",")
        airTempF = float(humidLis[4]) * 9/5 + 32
        return humid, airTempC, airTempF, dewPoint
    except:
        print("Humidity Reading Failed")

def getTemp():
    try:
        temReadC = temSens.query("R", processing_delay = 1000)
        temReadC = temReadC.data.decode("utf-8")
        temReadF = float(temReadC) * 9/5 + 32
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
            
        mins = mins + 1
        if mins == 30:
            try:
                takePic()
                mins = 0
                print("Took picture")
            except:
                print("Failed to take picture")
                mins = 25
        sleep(30)
    except:
        print("Loop failed")
        sleep(5)