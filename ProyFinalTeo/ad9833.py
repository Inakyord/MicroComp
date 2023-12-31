######################################################
###************************************************###
###                                                ###
###        Programa para controlar por SPI         ###
###           el módulo AD9833 con ayuda           ###
###            de la Raspberry Pi Pico             ###
###                                                ###
###************************************************###
######################################################

# By Kipling Crossing
# Link: https://github.com/KipCrossing/Micropython-AD9833
# Modified by Inaky Ordiales

class AD9833(object):

    # Clock Frequency
    ClockFreq =  15000000
    freq = 10000
    shape_word = 0x2000

    def __init__(self, spi, ss):
        self.spi = spi
        self.ss = ss

    # function for splitting hex into high and low bits
    def _bytes(self, integer):
        return divmod(integer, 0x100)

    def _send(self, data):
        high, low = self._bytes(data)
        msg = bytearray()
        msg.append(high)
        msg.append(low)
        
        self.ss.value(0)
        self.spi.write(msg)
        self.ss.value(1)

    def set_freq(self, freq):
        self.freq = freq

    def set_type(self, inter):
        if inter == 1:
            self.shape_word = 0x2020
        elif inter == 2:
            self.shape_word = 0x2002
        else:
            self.shape_word = 0x2000

    @property
    def shape_type(self):
        if self.shape_word == 0x2020:
            return "Cuadrada"
        elif self.shape_word == 0x2002:
            return "Triangular"
        else:
            return "Senoidal"

    def send(self):
        # Calculate frequency word to send
        word = hex(int(round((self.freq*2**28)/self.ClockFreq)))

        # Split frequency word onto its seperate bytes
        MSB = (int(word, 16) & 0xFFFC000) >> 14
        LSB = int(word, 16) & 0x3FFF

        # Set control bits DB15 = 0 and DB14 = 1; for frequency register 0
        MSB |= 0x4000
        LSB |= 0x4000

        self._send(0x2100)
        # Set the frequency
        self._send(LSB)  # lower 14 bits
        self._send(MSB)  # Upper 14 bits
        # Set the shape
        # square: 0x2020, sin: 0x2000, triangle: 0x2002
        self._send(self.shape_word)
        
    def info(self):
        # Imprime información de la onda actual
        print("\nForma: "+str(self.shape_type))
        print("Frecuencia = "+str(self.freq))