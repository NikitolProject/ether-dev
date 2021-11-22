# EtherBot

### Complete instructions for installing the bot, installing its 
### dependencies and launch the bot itself.
#

# Installing the bot and its dependencies

### (Debian / Ubuntu)

```bash
apt update && apt upgrade && apt install git
apt install python3 && apt install python3-pip
git clone https://github.com/NikitolProject/ether-dev
cd ether-dev
pip3 install -r requirements.txt
```

### Archlinux

```bash
sudo pacman -Syu
sudo pacman -S git
sudo pacman -S python3
curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
git clone https://github.com/NikitolProject/ether-dev
cd ether-dev
pip3 install -r requirements.txt
```
#
# Starting and shutting down the bot or its services

### To start or disable the entire bot

```bash
python3 main.py start # to launch
python3 main.py stop # to stop
```

### To start or disable a specific service

```bash
python3 main.py -s НазваниеСервиса start # to launch
python3 main.py -s НазваниеСервиса stop # to stop
```
