# includes
import time
import serial

from twilio.rest import Client

import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
from pad4pi import rpi_gpio

from gpiozero import DistanceSensor

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from generate import Customer, Base, Rate
engine = create_engine('sqlite:///shop.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

dtLastMessage = None

# methods
def keypadHandler(key):
    global keypad_enable
    global key_buffer
    if keypad_enable:
        print key
        lcd.write_string(str(key))
        key_buffer.append(key)
    else:
        discard = key

def inputCheck(inputLength):
    global keypad_enable
    if len(key_buffer) == inputLength:
        keypad_enable = False

def keypadInput(inputLength):
    global key_buffer
    global keypad_enable
    key_buffer = []
    keypad_enable = True
    try:
        while keypad_enable:
            inputCheck(inputLength)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print "KeyboardInterrupt"

def motor_set_clockwise():
    GPIO.output(motor_in1, True)
    GPIO.output(motor_in2, False)

def motor_set_anticlockwise():
    GPIO.output(motor_in1, False)
    GPIO.output(motor_in2, True)

def calcCustLevel(amount):
    if   amount > 0   and amount <= 50 :
        return 1
    elif amount > 50  and amount <= 150:
        return 2
    elif amount > 150 and amount <= 400:
        return 3
    elif amount > 400 and amount <= 750:
        return 4
    else:
        return 5

def reset():
    keypad_enable = False
    key_buffer = []

def measureDistance():
    val = []
    for i in xrange(5):
        val.append(Sensor.distance)
        time.sleep(0.15)
    avg = 0.0
    for x in val:
        avg = avg + x/5
    print "ultrasonic: " + str(avg)
    return avg

def measureWeight():
    val = []
    for i in xrange(5):
        read_serial=ser.readline()
        val.append(float(read_serial.strip()))
    avg = 0.0
    for x in val:
	print x
        avg = avg + x/5
    print "weight: " + str(avg)

def sendWarningMessage():
    global dtLastMessage
    now = dt.now()
    # 75% already checked
    if dt.time(now).hour > 8 and dt.time(now).hour < 18: # limit messages to working hours
        if dtLastMessage:
            delta = now - dtLastMessage
            if delta.days > 0:
                message = client.messages.create(
                                              from_='+14582197834',
                                              body='Bin is almost full, please empty it soon!',
                                              to='+918989034362'
                                          )

                print message.sid
                dtLastMessage = now
        else:
            message = client.messages.create(
                                          from_='+14582197834',
                                          body='Bin is almost full, please empty it soon!',
                                          to='+918989034362'
                                      )

            print message.sid
            dtLastMessage = now

def sendCriticalMessage():

    global dtLastMessage
    now = dt.now()
    # 90%, else components might get damaged
    if dt.time(now).hour > 8 and dt.time(now).hour < 18: # limit messages to working hours
        if dtLastMessage:
            delta = now - dtLastMessage
            if delta.seconds > (12 * 3600): # if more than half a day has elapsed
                message = client.messages.create(
                                              from_='+14582197834',
                                              body='Bin is completely full, please empty it immediately!',
                                              to='+918989034362'
                                          )

                print message.sid
                dtLastMessage = now
        else:
            message = client.messages.create(
                                          from_='+14582197834',
                                          body='Bin is completely full, please empty it immediately!',
                                          to='+918989034362'
                                      )

            print message.sid
            dtLastMessage = now


def isFull():

    distance = measureDistance()
    weight = measureWeight()
    if distance < 20 or weight > 7:
        sendCriticalMessage()
        return True
    elif distance < 25 or weight > 5:
        sendWarningMessage()
        return False
    else:
        return False

# setup

account_sid = <ADD_SID_HERE>
auth_token = <ADD_AUTH_TOKEN_HERE>
client = Client(account_sid, auth_token)

# i2c
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
              cols=20, rows=2, dotsize=8,
              charmap='A02',
              auto_linebreaks=True,
              backlight_enabled=True)


# keypad
KEYPAD = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
    ["*", 0, "#"]
]

ROW_PINS = [25, 8, 7, 26]
COL_PINS = [12, 19, 16]
factory = rpi_gpio.KeypadFactory()
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)
keypad.registerKeyPressHandler(keypadHandler)
keypad_enable = False
key_buffer = []

# motor driver
motor_in1 = 20
motor_in2 = 21
motor_en  = 4
GPIO.setup(motor_in1, GPIO.OUT)
GPIO.setup(motor_in2, GPIO.OUT)
GPIO.setup(motor_en, GPIO.OUT)
pwm=GPIO.PWM(motor_en, 100)
GPIO.output(motor_en, True)
pwm.start(0)

# distance sensor
Sensor = DistanceSensor(echo=24, trigger=18)

# weight sensor serial
ser = serial.Serial('/dev/ttyUSB0',9600)











# main script
while not isFull(): # change to while later for transactions
    lcd.clear()
    lcd.write_string('Enter phone no.')
    lcd.crlf()
    lcd.cursor_mode = "blink"

    # input
    keypadInput(10)

    lcd.cursor_mode = "hide"
    lcd.clear()
    lcd.write_string('Verifying...')
    time.sleep(2)

    # construct string
    phone_string = ""
    for i in key_buffer:
        phone_string = phone_string + str(i)
    print phone_string

    # database query
    customer = session.query(Customer).filter(Customer.phone_no==phone_string).first()

    if customer is not None:
        print "Customer found!"

        lcd.cursor_mode = "blink"
        lcd.clear()
        lcd.write_string('Press 1')
        lcd.crlf()
        lcd.write_string('for paper: ') # text may scroll to diplay other options

        keypadInput(1)

        lcd.cursor_mode = "hide"

        if key_buffer[0] == 1: # paper waste selected

            # door opens
            # down

            old_weight = measureWeight()

            motor_set_anticlockwise()
            pwm.ChangeDutyCycle(100)
            time.sleep(2.3)
            pwm.ChangeDutyCycle(0)

            lcd.clear()
            lcd.write_string('After use, press')
            lcd.crlf()
            lcd.write_string('any key: ')
            lcd.cursor_mode = "blink"

            keypadInput(1)
            lcd.cursor_mode = "hide"

            # door close
            # up
            motor_set_clockwise()
            pwm.ChangeDutyCycle(100)
            time.sleep(2.3)
            pwm.ChangeDutyCycle(0)

            # weighing
            new_weight = measureWeight()
            weight_deposited = new_weight - old_weight

            # display weight
            lcd.clear()
            lcd.write_string('Weight deposited')
            lcd.crlf()
            lcd.write_string(str(weight_deposited))

            time.sleep(3)

            # balance calculation
            # pay = mod_rate * weight
            # mod_rate = level*0.25 + item.rate
            # level = customer.total_amount lies between 0 50 150 400 750 1200

            item = session.query(Rate).filter(Rate.item_name=='paper').first()
            base_rate = item.base_rate
            customer.total_amount

            level = calcCustLevel(customer.total_amount)
            mod_rate = level*0.25 + base_rate
            pay = mod_rate * weight_deposited

            # put in atomic transaction
            customer.balance = customer.balance + pay
            customer.total_amount = customer.total_amount + pay

            session.commit()

            # display updated balance and level up updates
            lcd.clear()
            lcd.write_string('New balance:')
            lcd.crlf()
            lcd.write_string(str(customer.balance))
            time.sleep(5)

            new_level = calcCustLevel(customer.total_amount)
            if (new_level > level):
                # display level upgrade message
                lcd.clear()
                lcd.write_string('Level up!')
                lcd.crlf()
                lcd.write_string('Congratulations!')
                time.sleep(5)

            lcd.clear()
            lcd.write_string('Thank you for ')
            lcd.crlf()
            lcd.write_string('helping Earth!')
            time.sleep(5)



            # check filled level at the end of transaction
            # if warning level issue warning
            # if filled lockdown machine
            if isFull():
                lcd.clear()
                lcd.write_string('Machine full!')
                lcd.crlf()
                lcd.write_string('Please empty!')
                time.sleep(10)
            reset()
            # reset values for next transaction

        else:
            # paper not selected, error
            # reset values for next transaction
            lcd.clear()
            lcd.write_string('Invalid option')
            lcd.crlf()
            lcd.write_string('Please try again')
            time.sleep(10)
            reset()
    else: # auth fails
        lcd.clear()
        lcd.write_string('User not found')
        lcd.crlf()
        lcd.write_string('Please try again')
        time.sleep(3)
        # display error
        # reset values for next transaction
        reset()
lcd.clear()
lcd.write_string('Machine full!')
lcd.crlf()
lcd.write_string('Please empty!')
time.sleep(10)
reset()
