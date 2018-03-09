import time
import serial
import datetime
import csv
import codecs

# your TTY
tty = 'COM7'
ttyb = 57600
# your devaddr here
#devaddr = "ABCDEF01"
#device = "nodes/" + devaddr
# config.append("mac reset 868")
# config.append("mac set pwridx 5")
# config.append("mac set dr 5")
# config.append("mac set adr off")
# config.append("mac set nwkskey 2B7E151628AED2A6ABF7158809CF4F3C")
# config.append("mac set appskey 2B7E151628AED2A6ABF7158809CF4F3C")
# config.append("mac set devaddr "+devaddr)
# config.append("mac save")
# config.append("mac join abp")

def send(data, p):
    data_bytes = data.encode('ascii')
    p.write(data_bytes + b"\x0d\x0a")
    #?data_bytes.rstrip()
    print(data)
    time.sleep(0.04)
    rdata = p.readline()
    rdata = rdata[:-2]
    print(rdata)
    #?return rdata

def hextranslate(s):
    res = ""
    if len(s) % 2 == 0 :
        for i in range(int(round(len(s) / 2))):
            realIdx = i * 2
            res = res + chr(int(s[realIdx:realIdx + 2], 16))
        return res
    else:
        return s

def sendd(data, p):
    data_bytes = data.encode()
    p.write(data_bytes + b"\x0d\x0a")
    time.sleep(0.1)


def configuration(type):
    config = []
    # config.append("sys factoryRESET")
    config.append("sys reset")
    config.append("mac pause")
    config.append("radio set freq 868250000")
    config.append("radio set pwr 14")
    config.append("radio set afcbw 125")
    config.append("radio set rxbw 125")
    config.append("radio set fdev 5000")
    config.append("radio set prlen 8")
    config.append("radio set crc on")
    config.append("radio set cr 4/8")
    config.append("radio set wdt 0")
    config.append("radio set sync 12")
    config.append("radio set bw 125")
    if type == 1:
        configuration.name = 'LoraSF12'
        config.append("radio set mod lora")
        config.append("radio set sf sf12")
    elif type == 2:  # Lora SF7
        configuration.name = 'LoraSF7'
        config.append("radio set mod lora")
        config.append("radio set sf sf7")
    elif type == 3:  # FSK
        configuration.name = 'fsk'
        config.append("radio set mod fsk")
        # config.append("radio set bitrate 40000")
    for c in config:
        send(c, p)



def get_packet():
    get_packet.circle = 0
    while get_packet.circle < 24:
        sendd("radio rx 1000", p)
        s = p.readline()
        if (s == b'ok\r\n')|(s == b'busy\r\n'):
            s = p.readline()
        get_packet.check = s[0:8]
        if (get_packet.check == b'radio_rx'):
            s_post = s.decode('ascii')          #проверка - получили?
            # if ((s != b'radio_err\r\n')|(s != b'busy\r')|(s != b'ok\r\n'))&(s != b'')&(len(s.decode('utf-8')) > 4):
            s_post = s_post.replace("radio_rx  ", "")
            get_packet.data = s_post.replace("\r\n", "")    #запись полученных данных
            # global h
            # h = get_packet.data

            get_packet.dehex = hextranslate(get_packet.data)    #расшифровка полученных данных

            sendd("radio get snr", p)           #radio get snr
            ans = p.readline()
            if ans == b'ok\r\n':
                tmp = p.readline()
                tmp = tmp.decode('ascii')
                tmp = tmp.replace('\r\n', '')
                # tmp = tmp.replace("b\\", "")
                get_packet.snr = tmp
            else:
                tmp = ans
                tmp = tmp.decode('ascii')
                tmp = tmp.replace('\r\n', '')
                # tmp = tmp.replace("b\\", "")
                get_packet.snr = tmp
            return 1
            # print(get_packet.data)
            # print(get_packet.dehex)
        # if not hasattr(get_packet, 'data'):
        #     get_packet.data = s_post
        elif(get_packet.check == b'radio_err\r\n'):     #проверка неполучили? или получили с ошибкой
            get_packet.circle = get_packet.circle + 1
            continue
        get_packet.configType = configuration.name
        get_packet.datetime = datetime.datetime.now()
        # global j
        # j = get_packet.circle

            # print(s_post)
            # print(configuration.name)

        time.sleep(0.5)
        get_packet.circle = get_packet.circle + 1
    return 0

p = serial.Serial(tty, ttyb, timeout=1)


#time.sleep(0.5)

print("READY FOR RX")

conf = 1
past = None

while True:
    configuration(conf)
    s = 0
    while s < 10:
        if get_packet():
            Data = str(get_packet.datetime) + ';' + str(get_packet.configType) + ';' + str(get_packet.data) + ';' + str(get_packet.dehex)+ ';' + str(get_packet.snr) + '\r'
        else:
            Data = str(datetime.datetime.now()) + ';' + str(configuration.name) + ';' + 'None'
        fd = open('data.csv', 'a')
        fd.write(Data)
        fd.close()
        s = s + 1
        print(Data)
    conf += 1
    if conf > 3: conf = 1