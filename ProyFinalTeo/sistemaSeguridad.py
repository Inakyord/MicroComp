######################################################
###************************************************###
###                                                ###
###    PROYECTO FINAL: SISTEMA DE SEGURIDAD        ###
###                                                ###
###                                                ###
###    Se simula un sistema de seguridad que se    ###
###   bloquea en cuanto detecta un intruso cerca   ###
###  del sensor. Está implementado en dos núcleos  ###
###  y se comunica via USB para dejar un Log en la ###
###  computadora de registro.                      ###
###                                                ###
###************************************************###
######################################################


# Importamos las bibliotecas que usaremos
from machine import Pin     # Usar pines Pi Pico
from machine import PWM     # Usar Pulse Width Modulation en la Pi Pico
from time import ticks_ms   # Herramienta de tiempo para evitar rebotes
import _thread              # Hilo para permitir trabajar con dos núcleos
import utime                # Biblioteca para retardos


############################################
####XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX####
############################################
####                                    ####
####    Declaración de las Funciones    ####
####    de los Pines.                   ####
####                                    ####
############################################
####XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX####
############################################

# Para el sensor Ultrasónico
Trigger = Pin(26,Pin.OUT)
Echo    = Pin(27,Pin.IN, Pin.PULL_DOWN)

# Para botón desbloqueo
Boton   = Pin(15, Pin.IN, Pin.PULL_UP)

# Para el servo
pwmServo = PWM(Pin(28))
pwmServo.freq(50)

# Para los leds
LedRojo = Pin(21, Pin.OUT)
pwmLed1  = PWM(Pin(20))
pwmLed2  = PWM(Pin(19))
pwmLed3  = PWM(Pin(18))
pwmServo.freq(50)
pwmLed1.freq(1000)
pwmLed2.freq(1000)
pwmLed3.freq(1000)

# Valores PWM para el servo
abierto   = 4000  # valor para abrir el servo
cerrado   = 6350  # valor para cerrar el servo

# Variables utilizadas
alarma = 0
cuenta = 0
debounce_time = 0
botonpres = 0

# Valores iniciales
pwmServo.duty_u16(abierto)
pwmLed1.duty_u16(7000)
pwmLed1.duty_u16(7000)
pwmLed1.duty_u16(7000)
LedRojo.high()


########################################
###                                  ###
### CONFIGURACIONES INTERRUPCIONES   ###
###                                  ###
### al apretar un botón se lleva una ###
### interrupción para liberar el     ###
### servo en caso de estar cerrado,  ###
###  cuidando que no haya un rebote  ###
###                                  ###
########################################

# Definición interrupcion botón
def callback(Boton):
    global alarma, botonpres, debounce_time
    if (ticks_ms() - debounce_time) > 250:
        debounce_time = ticks_ms()
        if alarma == 1:
            botonpres = 1

Boton.irq(trigger=Pin.IRQ_FALLING, handler=callback)


###################################
###                             ###
### Función para leer distancia ###
###                             ###
###################################

def read():
    Trigger.low()
    utime.sleep(0.1)

    # avienta ondas por 4us
    Trigger.high()
    utime.sleep_us(4)
    Trigger.low()

    # calcula el tiempo inicial
    while Echo.value() == 0:
        tiempoInicio = utime.ticks_us()

    # calcula el tiempo final
    while Echo.value() == 1:
        tiempoFin = utime.ticks_us()

    # hace la conversión entre tiempo y distancia según la
    #   velocidad de las ondas.
    tiempo = tiempoFin - tiempoInicio
    distancia = (tiempo * 0.043) / 2
    distancia = round(distancia, 0)
    
    # regresa como resultado la distancia en cm
    return distancia


##################################
###                            ###
###       SEGUNDO NÚCLEO       ###
###                            ###
##################################

def segundoNucleo():
    global alarma, cuenta, botonpres, LedRojo, pwmLed1, pwmLed2, pwmLed3
    # Valores PWM
    prendido  = 7000  # valor para prender led
    medioAlto = 3000  # valor para poner led medio alto
    medioBajo = 1000  # valor para poner led medio bajo
    apagado   = 0     # valor para apagar led
    
    secuencia = 0     # identificador inicial secuencia leds
    ante = 0          # controlar si se acaba de cerrar
    
    # asignación valores iniciales
    valor1 = apagado
    valor2 = apagado
    valor3 = apagado
    LedRojo.low()
    
    
    # ciclo infinito, programa principal segundo núcleo
    while True:
        
        utime.sleep(0.2)
        
        # si hay alarma no mueve leds, checa por el botón de liberación.    
        if alarma == 1:
            if ante == 0:
                LedRojo.high()
                pwmLed1.duty_u16(apagado)
                pwmLed2.duty_u16(apagado)
                pwmLed3.duty_u16(apagado)
                print("\n¡¡¡ Se ha activado la alarma !!!")
                print("Es la vez número: "+str(cuenta)+".\n")
                ante = 1
            if botonpres == 1:
                LedRojo.low()
                alarma = 0
                botonpres = 0
                print("\nSe ha desactivado la alarma.\n")
                ante = 0
            continue
        
        # Si no está activada la alarma hace rutina con leds
        pwmLed1.duty_u16(valor1)
        pwmLed2.duty_u16(valor2)
        pwmLed3.duty_u16(valor3)
        secuencia += 1
        
        if secuencia == 1:
            valor3 = valor2
            valor2 = valor1
            valor1 = prendido
        elif secuencia == 2:
            valor3 = valor2
            valor2 = valor1
            valor1 = medioAlto
        elif secuencia == 3:
            valor3 = valor2
            valor2 = valor1
            valor1 = medioBajo
        elif secuencia == 4:
            valor3 = valor2
            valor2 = valor1
            valor1 = apagado
        elif secuencia == 5:
            valor3 = valor2
            valor2 = valor1
            valor1 = apagado
        elif secuencia == 6:
            valor3 = valor2
            valor2 = valor1
            valor1 = apagado
        elif secuencia == 7:
            valor1 = valor2
            valor2 = valor3
            valor3 = prendido
        elif secuencia == 8:
            valor1 = valor2
            valor2 = valor3
            valor3 = medioAlto
        elif secuencia == 9:
            valor1 = valor2
            valor2 = valor3
            valor3 = medioBajo
        elif secuencia == 10:
            valor1 = valor2
            valor2 = valor3
            valor3 = apagado
        elif secuencia == 11:
            valor1 = valor2
            valor2 = valor3
            valor3 = apagado
        elif secuencia == 12:
            valor1 = valor2
            valor2 = valor3
            valor3 = apagado
            secuencia = 0

#########################################################################################
###                                                                                   ###
###                      FIN DEL PROGRAMA DEL SEGUNDO NÚCLEO                          ###
###                                                                                   ###
#########################################################################################



#################################################
######*************************************######
######                                     ######
######   Código principal del programa     ######
######                                     ######
######*************************************######
#################################################

# Iniciamos el hilo de ejecución para el segundo núcleo
_thread.start_new_thread(segundoNucleo, ())

# Variable para saber cuando abrir
ante = 0

# Hilo principal, primer núcleo
while True:    
    
    # si está activada la alarma no hace nada
    if alarma == 1:
        continue
    
    # si por primera vez se cicla tras desactivar, se abre
    if ante == 1:
        pwmServo.duty_u16(abierto)
        ante = 0
    
    # lee y muestra la distancia
    lectura = read()
    print("El objeto se encuentra a una distancia de ", lectura," cm")
    
    # checa si está demasiado cerca y cierra
    if lectura < 10:
        pwmServo.duty_u16(cerrado)
        cuenta += 1
        alarma = 1
        ante = 1
    
    utime.sleep(0.1)
    
    
#########################################################################################
###                                                                                   ###
###                           FIN DEL PROGRAMA DEL PRIMER NÚCLEO                      ###
###                                                                                   ###
#########################################################################################