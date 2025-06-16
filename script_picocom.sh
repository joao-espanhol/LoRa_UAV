picocom -b 115200 /dev/ttyUSB0 | ts '[%Y-%m-%d %H:%M:%S]' | tee logpicocom.txt
