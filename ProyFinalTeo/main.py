######################################################
###************************************************###
###                                                ###
###        Proyecto Final, señales RP2             ###
###                                                ###
###************************************************###
######################################################

#######################################################################
#######################################################################
####                                                               ####
####  Simulador de un circuito paso banda en la RASPBERRY PI PICO  ####
####                                                               ####
#######################################################################
#######################################################################
####                 C1              R2                            ####
####            -----||------------/\/\/\-----------               ####
####           +             |               |      +              ####
####                         >               |                     ####
####          Vi(t)       R1 <            C2 =     Vo(t)           ####
####                         >               |                     ####
####           -             |               |      -              ####
####            ------------------------------------               ####
####                                                               ####
#######################################################################
#######################################################################

#######################################################################
#######################################################################
####                                                               ####
####            Valores y función de transferencia                 ####
####                                                               ####
#######################################################################
#######################################################################
####                                                               ####
####     C1   = 100nF                   C2   = 100nF               ####
####     R1   = 16kOhm                  R2   = 8kOhm               ####
####     C1R1 = 1.6m                    C2R2 = 0.8m                ####
####                                                               ####
####     Fc1  = 99.5 Hz                 Fc2  = 199 Hz              ####
####                                                               ####
####                                                               ####
####  HR(s) = sRC / (sRC +1)            HC(s) = 1 / (sRC +1)       ####
####  HR(s) = s(0.0016)/(s(0.0016)+1)   HC(s) = 1 / (s(0.0008)+1)  ####
####                                                               ####
####  HR(s)*HC(s) = s(0.0016) / ( s^2(1.28x10^-6)+s(0.0024)+1)     ####
####                                                               ####
#######################################################################
####                                                               ####
####    EN MATLAB:                                                 ####
####                                                               ####
####  sys = tf ( [0.0016 0], [0.00000128 0.0024 1] )               ####
####                                                               ####
####                   0.0016 s                                    ####
####  sys = -----------------------------                          ####
####         1.28e-06 s^2 + 0.0024 s + 1                           ####
####                                                               ####
####                                                               ####
####  sysd = c2d (sys, 0.000125, 'tustin')                         ####
####                                                               ####
####           0.06974 z^2 - 0.06974                               ####
####  sysd = -------------------------                             ####
####           z^2 - 1.78 z + 0.7908                               ####
####                                                               ####
#######################################################################
#######################################################################
####                                                               ####
####   ECUACION EN DIFERENCIAS:                                    ####
####                                                               ####
#### Vo(k) =  0.06974Vi(k) + 0Vi(k-1) - 0.06974Vi(k-2) +           ####
####           + 1.78Vo(k-1) - 0.7908Vo(k-2)                       ####
####                                                               ####
#######################################################################
#######################################################################
####                                                               ####
####          UNIVERSIDAD NACIONAL AUTÓNOMA DE MÉXICO              ####
####                  FACULTAD DE INGENIERÍA                       ####
####                     MICROCOMPUTADORAS                         ####
####                                                               ####
#######################################################################
#######################################################################


# Importamos las bibliotecas necesarias
from machine import Pin       # Usar pines Pi Pico
from machine import UART      # Protocolo UART para MatLab
from machine import SPI       # Protocolo SPI para ad9833
from machine import ADC       # Convertidor analógico-digital
from ad9833 import AD9833     # Estructura para controlar el AD9833
from time import sleep        # retardo en s
from time import sleep_us     # retardo en us
from time import ticks_ms     # herramienta de tiempo
import struct                 # convertir de float a hexadecimal


##################################
###                            ###
### CONFIGURACIONES INICIALES  ###
###                            ###
##################################

# Hacer que el CPU trabaje a 24 MHz
machine.freq(240000000)

# Declarar convertidor ADC por canal 0
adc0 = ADC(0)

# Declara UART para comunicarse con MATLAB
uart0 = UART(0, baudrate=460800, tx=Pin(0), rx=Pin(1))

# Usamos led de la tarjeta como registro
P25 = Pin(25, Pin.OUT)


##################################
###                            ###
###   CONFIGURACIONES AD9833   ###
###                            ###
##################################

# Declarar SPI para controlar el ad9833
cs = Pin(17, Pin.OUT) # activación esclavo spi
spi0 = SPI( 0,
            baudrate=9600,
            polarity=1,
            phase=1,
            bits=8,
            firstbit=machine.SPI.MSB,
            sck=machine.Pin(18),
            mosi=machine.Pin(19),
            miso=machine.Pin(16))

# Variables para el control de la onda (AD9833)
frecuencia = 0
forma = 0
debounce_time = 0
botonpres = 0
    
# Botones para el control de la señal (AD9833)
botonForma = Pin(14, Pin.IN, Pin.PULL_UP)
botonFrec  = Pin(15, Pin.IN, Pin.PULL_UP)

# Inicialización de la señal del AD9833
wave = AD9833(spi0, cs)
wave.set_freq(frecuencia+25)
wave.set_type(forma+1)
wave.send()
sleep(0.5)
wave.info()
sleep(0.5)


########################################
###                                  ###
### CONFIGURACIONES INTERRUPCIONES   ###
###                                  ###
### al apretar un botón se lleva una ###
### interrupción para modificar la   ###
### onda, cuidando que no haya un    ###
### rebote al apretarlo.             ###
###                                  ###
###                                  ###
########################################

# Definición interrupciones onda
def callback(botonForma):
    global botonpres, debounce_time
    if (ticks_ms() - debounce_time) > 250:
        debounce_time = ticks_ms()
        botonpres = 1

botonForma.irq(trigger=Pin.IRQ_FALLING, handler=callback)


def callback(botonFrec):
    global botonpres, debounce_time
    if (ticks_ms() - debounce_time) > 250:
        debounce_time = ticks_ms()
        botonpres = 2

botonFrec.irq(trigger=Pin.IRQ_FALLING, handler=callback)


###########################################
###                                     ###
###   Variables para lectura de señaes  ###
###                                     ###
###########################################

# Declaración de variables y constantes usadas
muestras = 500
entradas = [0] * muestras
salidas  = [0] * muestras
conv_bytes = bytearray(4*2*muestras)
factor = 3.3/(65535)  # Factor de conversion de digital a voltaje

# Coeficientes de la Función de Transferencia
CTE_A0 =  0.06974
CTE_A1 =  0.0
CTE_A2 = -0.06974
CTE_B1 =  1.78
CTE_B2 = -0.7908

# Condiciones iniciales de las entradas y salidas
UK   = 0.0  # u(k)
UK1  = 0.0  # u(k-1)
UK2  = 0.0  # u(k-2)
YK   = 0.0  # y(k)
YK1  = 0.0  # y(k-1)
YK2  = 0.0  # y(k-2)
Leer = 0.0


###########################################
###                                     ###
###   Código principal del programa     ###
###                                     ###
###   LECTURA Y PROCESAMIENTO DE LAS    ###
###              SEÑALES                ###
###                                     ###
###########################################

while True:
    
    # Checa si se presionó para cambiar la forma
    if botonpres == 1:
        forma = (forma + 1) % 3
        wave.set_type(forma + 1)
        wave.send()
        wave.info()
        botonpres = 0
    
    # Checa si se presionó para cambiar la frecuencia 
    if botonpres == 2:
        frecuencia = (frecuencia + 25) % 300
        wave.set_freq(frecuencia + 25)
        wave.send()
        wave.info()
        botonpres = 0
    
    
    if uart0.any() > 0:
        
        LLAVE = uart0.read(1)      # Lee 1 byte recibido
        
        # Se espera a que se ingrese la llave correspondiente
        if "U" in LLAVE:
            P25.on()
            
            for i in range(0,muestras):
                
                # Armado de la ecuación en diferencias
                YK = CTE_A0*UK + CTE_A1*UK1 + CTE_A2*UK2 + CTE_B1*YK1 + CTE_B2*YK2
                
                # Actualiza I/O para la próxima iteración
                UK2 = UK1  # u(k-1) --> u(k-2)
                UK1 = UK   # u(k)   --> u(k-1)
                YK2 = YK1  # y(k-1) --> y(k-2)
                YK1 = YK   # y(k)   --> y(k-1)
                
                # Lectura de la señal digital y conversión a valor analógico
                Leer = adc0.read_u16() * factor
                
                UK = Leer
                entradas[i] = UK
                salidas[i]  = YK+1.65 # se compensa el offset de la salida
                sleep_us(80)


            P25.off()
            
            # Empaquetamiento de los datos en bytearrays
            conv_bytes = bytearray(struct.pack("f", entradas[0]))
            conv_bytes = conv_bytes + bytearray(struct.pack("f", salidas[0]))
            
            for i in range(1,muestras):
                conv_bytes = conv_bytes + bytearray(struct.pack("f", entradas[i]))
                conv_bytes = conv_bytes + bytearray(struct.pack("f", salidas[i]))
            
            # Envío de los datos
            uart0.write(conv_bytes)


#########################################################################################
###                                                                                   ###
###                           FIN DEL PROGRAMA                                        ###
###                                                                                   ###
#########################################################################################

