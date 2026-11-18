# Vzor konfigurace.
# Zkopíruj tento soubor jako config.py a vyplň vlastní hodnoty.
# config.py je v .gitignore, takže se heslo nedostane do gitu.

# Wi-Fi (Pico W umí jen 2,4 GHz, eduroam nefunguje)
SSID = "nazev_site"
PSWD = "heslo"

# MQTT broker = IP počítače s Mosquittem ve stejné síti (zjistíš: hostname -I)
MQTT_BROKER = "172.20.10.2"
