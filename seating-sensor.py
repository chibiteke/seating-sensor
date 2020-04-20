from datetime import datetime
import time
import RPi.GPIO as GPIO
import requests
import logging
import configparser

MYFORMAT = '[%(asctime)s]%(filename)s(%(lineno)d): %(message)s'
logging.basicConfig(
    filename='/var/www/html/sensor/sensor.log',
    filemode='w',  # Default is 'a'
    format=MYFORMAT,
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)
# logging.debug('1. This is debug.')
# logging.info('2. This is info.')
# logging.warning('3. This is warning.')
# logging.error('4. This is error.')
# logging.critical('5. This is critical.')

# インターバル
INTERVAL = 5
# スリープタイム
SLEEPTIME = 10
# 使用するGPIO
GPIO_PIN = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.IN)


config_ini = configparser.ConfigParser()
config_ini .read('/home/pi/sensor/config.ini', 'UTF-8')

# 通知メール送信用スクリプト
gas_mail = config_ini['Google Apps Script']['MAIL_SEND']
# 日記スプレッド―シート記録スクリプト
gas_diary = config_ini['Google Apps Script']['DIARY']


if __name__ == '__main__':
    try:
        # 起動
        logging.info("起動しました")
        send_message = "?message1=起動しました&message2&message3"
        res = requests.get(gas_mail + send_message)
        logging.debug(res.text)
        res = requests.get(gas_diary + send_message)
        logging.debug(res.text)

        seet_cnt = 1
        away_cnt = 1
        while True:
            # センサー感知
            if(GPIO.input(GPIO_PIN) == GPIO.HIGH):
                logging.info(str("{0:05d}".format(seet_cnt)) + "回目の人感知")

                send_message = "?message1=着席&message2={0:05d}&message3".format(seet_cnt)

                if (seet_cnt == 5 * 60 / SLEEPTIME):
                    # 着席して5分経過したら日記に通知する
                    res = requests.get(gas_diary + send_message)
                    logging.debug(res.text)

                seet_cnt = seet_cnt + 1
                if(seet_cnt > (3 * 60 / SLEEPTIME)):
                    away_cnt = 1
                time.sleep(SLEEPTIME)

            else:
                logging.info(str("***{0:05d}".format(away_cnt)) + "回目の離席感知")

                send_message = "?message1=離席&message2&message3={0:05d}".format(away_cnt)

                if (away_cnt == 15 * 60 / SLEEPTIME):
                    # 離席して15分経過したら日記に通知する
                    res = requests.get(gas_diary + send_message)
                    logging.debug(res.text)

                away_cnt = away_cnt + 1
                if(away_cnt > (60 / SLEEPTIME)):
                    seet_cnt = 1
                time.sleep(SLEEPTIME)

    except KeyboardInterrupt:
        logging.info("終了処理中...")

    except Exception as e:
        logging.info(e.args)

    finally:
        GPIO.cleanup()
        logging.info("GPIO clean完了")
        send_message = "?message1=終了しました&message2&message3"
        res = requests.get(gas_diary + send_message)
        logging.info(res.text)
