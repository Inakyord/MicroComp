#include <16F877A.h>             // biblioteca del micro
#device ADC=10                   // establece el convertidor A/D en 10 bits resolución
#fuses HS,NOWDT,NOPROTECT,NOLVP  // parametros físicos - eléctricos del controlador
#use delay(clock=20000000)       // 20 MHz establece el reloj a utilizar
// utiliza estándar rs232 con la configuración:
//   transmite por portC.6 y recibe por portC.7 con 9600 bauds
#use rs232(baud=9600, xmit=PIN_C6, rcv=PIN_C7)
#define use_portd_lcd true       // establece el PORTD como conexión del display LCD
#include <lcd.c>                 //biblioteca para control de display LCD.
#org 0x1F00, 0x1FFF void loader16F877(void) {} // reserva la memoria donde esta el bootloader


float temperatura;   // variable para almacenar la lectura de temperatura
float voltaje;       // variable para almacenar la lectura de voltaje
float corriente;     // variable para almacenar la lectura de corriente
INT16 lectura;       // variable para guardar temporalmente lectura digital
int dentro;          // indica si se esta en el menú o dentro de medición
int estado;          // estado en el que está el menú
/*
Edo 0 --> *Temperatura
           Voltaje

Edo 1 -->  Temperatura
          *Voltaje

Edo 2 --> *Voltaje    
           Corriente

Edo 3 -->  Voltaje    
          *Corriente
*/

// Función para iniciar el LCD y presentar el proyecto
void inicioLCD() {
   lcd_gotoxy(2,1);  // posiciona cursor en (2,1)
   printf(lcd_putc," Equipo 5:\n"); //escribe los chars en el LCD
   lcd_gotoxy(2,2);
   printf(lcd_putc," Integrantes...");
   delay_ms(50);     // espera 50 ms
   lcd_gotoxy(1,2);
   printf(lcd_putc,"   Aurelio      ");
   delay_ms(50);
   lcd_gotoxy(1,2);
   printf(lcd_putc,"   Emilio       ");
   delay_ms(50);
   lcd_gotoxy(1,2);
   printf(lcd_putc,"   Inaky        ");
   delay_ms(50);
   lcd_gotoxy(1,2);
   printf(lcd_putc,"   Marcelo      ");
   delay_ms(50);
   lcd_gotoxy(1,1);
   printf(lcd_putc,"Proyecto final  ");
   lcd_gotoxy(1,2);
   printf(lcd_putc,"  :)            ");
   delay_ms(50);
}

// función para imprimir el menú según el estado actual
void imprimeMenu() {
   switch (estado){
      case 0:
         lcd_gotoxy(1,2);
         printf(lcd_putc,"   Voltaje V    ");
         lcd_gotoxy(1,1);
         printf(lcd_putc," * Temperatura C");
         break;
      case 1:
         lcd_gotoxy(1,1);
         printf(lcd_putc,"   Temperatura C");
         lcd_gotoxy(1,2);
         printf(lcd_putc," * Voltaje V    ");
         break;
      case 2:
         lcd_gotoxy(1,2);
         printf(lcd_putc,"   Corriente I  ");
         lcd_gotoxy(1,1);
         printf(lcd_putc," * Voltaje V    ");
         break;
      case 3:
         lcd_gotoxy(1,1);
         printf(lcd_putc,"   Voltaje V    ");
         lcd_gotoxy(1,2);
         printf(lcd_putc," * Corriente I  ");
         break;
      default:
         break;
   }
}

// función para imprimir la lectura según el estado actual.
void imprimeLectura() {
   lcd_gotoxy(1,1);
   switch (estado){
      case 0:
         set_adc_channel(0);     // Configura el canal 0 para usar
         delay_us(20);           // Retardo de 20 us
         lectura = read_adc();   // obtiene el resultado de A/D
         temperatura = lectura * 0.489; // ecuación lineal temper. °C
         printf(lcd_putc," Temperatura:   ");
         lcd_gotoxy(1,2);
         printf(lcd_putc,"    %04.1f  C     ", temperatura);
         break;
      case 1:
      case 2:
         set_adc_channel(1);     // Configura el canal 1 para usar
         delay_us(20);           // Retardo de 20 us
         lectura = read_adc();   // obtiene el resultado de A/D
         voltaje = lectura * 0.02;  // ecuación lineal voltaje V
         printf(lcd_putc," Voltaje:       ");
         lcd_gotoxy(1,2);
         printf(lcd_putc,"    %04.1f V      ", voltaje);
         break;
      case 3:
         set_adc_channel(4);     // Configura el canal 2 para usar
         delay_us(20);           // Retardo de 20 us
         lectura = read_adc();   // obtiene el resultado de A/D
         corriente = lectura * 4.89;   // ecuación lineal corriente mA
         printf(lcd_putc," Corriente:     ");
         lcd_gotoxy(1,2);
         printf(lcd_putc,"    %05.1f mA    ", corriente);
         break;
      default:
         break;
   }
}


// Control de interrupciones de los botones
#INT_RB
void port_rb(){
   // código de rutina de interrupción.

   int back  = !input_state(PIN_B4);   // estado botón back
   int enter = !input_state(PIN_B5);   // estado botón enter
   int down  = !input_state(PIN_B6);   // estado botón abajo
   int up    = !input_state(PIN_B7);   // estado botón arriba

   if (dentro) {  // checa si se está en lectura y sale a menú
      if (back) {
         dentro = 0;
         imprimeMenu();
      }
      return;
   }

   if (enter) {   // checa si está en menú y entra a lectura
      dentro = 1;
      imprimeLectura();
      return;
   }

   // cambia el estado según el botón (arriba o abajo) y imprime
   // el nuevo menú sólo cuando es necesario. Se usó una tabla
   // de transiciones para saber cuando se cambiaba de edo.
   switch (estado) {
      case 0:
         if (down) {
            estado = 1;
            imprimeMenu();
         }
         break;
      case 1:
      case 2:
         if (up) {
            estado = 0;
            imprimeMenu();
         }else if (down) {
            estado = 3;
            imprimeMenu();
         }
         break;
      case 3:
         if (up) {
            estado = 2;
            imprimeMenu();
         }
         break;
      default:
         break;
   } // end switch
   return;
}


// Función principal para el flujo del programa
int main() {

   //inicialización componentes
   enable_interrupts(INT_RB);    // habilita interrupciones de botones
   enable_interrupts(GLOBAL);    // habilita interrupciones globales
   lcd_init();                   // inicialización del display
   setup_port_a(ALL_ANALOG);     // Define el puerto A como analógico
   setup_adc(ADC_CLOCK_INTERNAL);// Define frecuencia de muestreo A/D
   // inicialización de variables
   estado = 0;
   dentro = 0;
   lectura = 0;
   temperatura = 0;
   voltaje = 0;
   corriente = 0;

   inicioLCD();   // inicia el LCD y presenta proyecto
   imprimeMenu(); // imprime el menú en su estado inicial

   // entra a un ciclo infinito donde si está dentro(lectura)
   // actualiza el valor que se muestra en el display cada 10ms
   while(true) {
      
      if (dentro){
         imprimeLectura();
      }
      delay_ms(10);
   } // end while
   
   return 0;

} //end main




/*

Menú:

 * Temperatura C
 * Voltaje V
 * Corriente I


Dentro:

----------------
 Temperatura:
    xx.x °C
----------------
 Voltaje:
     x.x V
----------------
 Corriente:
     x.x mA
----------------


Temperatura: [°C]
   temp = lectura * 0.4888 = lectura * 0.489;

Voltaje: [V]
   volt = lectura * 0.01999 = lectura * 0.02;

Corriente: [I]
   corriente = lectura * 4.888 = lectura * 4.89;



Tabla de transiciones de estados:

Estado     Botón arriba   Botón abajo     Cambio
 x0              0             0             0
  0              0             1             1
 x0              1             0             0
 x0              1             1             0
 x1              0             0             1
  1              0             1             3
  1              1             0             0
  1              1             1             0
 x2              0             0             2
  2              0             1             3
  2              1             0             0
  2              1             1             0
 x3              0             0             3
 x3              0             1             3
  3              1             0             2
  3              1             1             2


*/
