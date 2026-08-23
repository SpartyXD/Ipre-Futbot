from machine import Pin
from utime import sleep

def pin(l,in_out):
    return Pin(l, in_out)

led = pin("LED", Pin.OUT)

print("LED starts flashing...")
while True:
    led.toggle()
    sleep(1) # sleep 1sec
print("Finished.")




# ##### Librerias ####

# import network
# import socket
# import _thread
# # import rp2
# import sys
# import uasyncio
# from machine import Pin, PWM
# from time import sleep, sleep_ms, ticks_us, time_ns

# # Librerias Propias #
# # from cliente import iniciar_cliente
# from control_lib import flanco_bajada, flanco_subida, StopMotor, RotateCCW, RotateCW, move, C_PID
# from WiFi import connect, check_wifi


# ##### Definicion de pines #####

# # LEDS
# led = Pin("LED", Pin.OUT)       # Onboard LED

# ## Leds para debuggear
# led_verde = Pin(20, Pin.OUT)
# led_amarillo = Pin(19, Pin.OUT)
# led_azul = Pin(18, Pin.OUT)

# led_azul.off()
# led_verde.off()
# led_amarillo.off()
# led.off()

# # Driver 1
# d1_stby = Pin(3, Pin.OUT)
# ##  Motor 1
# d1_ina1 = Pin(2,Pin.OUT)
# d1_ina2 = Pin(1, Pin.OUT)
# d1_pwma = PWM(Pin(0))

# # Driver 2
# d2_stby = Pin(11, Pin.OUT)
# ##   Motor 2
# d2_ina1 = Pin(6,Pin.OUT)
# d2_ina2 = Pin(5, Pin.OUT)
# d2_pwma = PWM(Pin(4))
# ##   Rodillo
# d2_inb1 = Pin(12,Pin.OUT)
# d2_inb2 = Pin(13, Pin.OUT)
# d2_pwmb = PWM(Pin(14))

# # Encoder 1
# m1_enc1 = Pin(7, Pin.IN, Pin.PULL_UP)
# m1_enc2 = Pin(8, Pin.IN, Pin.PULL_UP)
# # Encoder 2
# m2_enc1 = Pin(9, Pin.IN, Pin.PULL_UP)
# m2_enc2 = Pin(10, Pin.IN, Pin.PULL_UP)

# # Solenoide
# sol = Pin(15, Pin.OUT)

# ##### Parametros Iniciales #####

# d1_pwma.freq(22_000)    
# d2_pwmb.freq(22_000)
# d1_stby.value(1)        # Enable the motor driver 1
# d2_pwma.freq(22_000)
# d2_stby.value(1)        # Enable the motor driver 2

# # velocidades de referencia iniciales
# vel_ref_1 = 0
# vel_ref_2 = 0

# #---------------------------------------------------------------------------
# ##### Server Conection #####

# # Funcion encargada de crear instancia de cliente y conectarse al servidor
# async def iniciar_cliente(ip, puerto, nombre_cliente, wlan, led_cliente):
#     global vel_ref_1
#     global vel_ref_2   
#     global sol 
    
#     while True:
#         if wlan.isconnected():
#             print("Iniciando coneccion al servidor...")
#             server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # DGRAM para UDP, al mandar constantemente las velocidades, no nos importa si alguna se pierde o corrompe
#             server_socket.connect((ip, puerto))
#             led.on()
#             print("Conectado al servidor")

#             # Enviar nombre o ID al servidor
#             server_socket.send(nombre_cliente.encode('utf-8'))
#             print("Identificacion enviada")
            
            
#             # Funcion que permite controlar el robot desde el servidor
#             while True:
#                 try:
#                     mensaje = server_socket.recv(1024).decode('utf-8')
#                     if mensaje:
#                         print(mensaje)
#                         vel_rec_1, vel_rec_2, solenoide, rodillo = mensaje.split(",")
#                         vel_ref_1, vel_ref_2 = int(vel_rec_1), int(vel_rec_2)
#                         sol.value(int(solenoide))
#                         if int(rodillo):
#                             RotateCW(100, d2_inb1, d2_inb2, d2_pwmb)
#                         else:
#                             StopMotor(d2_inb1, d2_inb2, d2_pwmb)
#                         print(f"vel 1 r: {vel_ref_1} RPM, vel 1 r: {vel_ref_2} RPM")
                        
#                 except KeyboardInterrupt:
#                     print("Server connection close")
#                     led.off()
#                     break
                
#                 await uasyncio.sleep_ms(100)
#         else:
#             pass
        
#         await uasyncio.sleep(1)
        
        
# ##### Close Loop #####
        
# # Funcion encargada de actualizar constantemente las velocidades
# def close_loop():
#     global vel_ref_1
#     global vel_ref_2
    
#     # Motor 1
#     m1_enc1_prev = 1
#     count_pulses_1 = 0
#     vel_lectura_1= 0.0
#     duty_1 = 0.0
#     error_1_prev = 0.0
#     integral_1 = 0.0
#     Kp_1 = 0.1
#     Ki_1 = 0.0
#     Kd_1 = 0.0
    
#     # Motor 2
#     m2_enc1_prev = 1
#     count_pulses_2 = 0
#     vel_lectura_2 = 0.0
#     duty_2 = 0.0
#     error_2_prev = 0.0
#     integral_2 = 0.0
#     Kp_2 = 0.1
#     Ki_2 = 0.0
#     Kd_2 = 0.0
    
#     calc_vel = 0            # cada iteracion del while
#     delta_t = 0
#     time_prev = time_ns()   # tiempo en nanosegundos al iniciar
    
#     while True:
#         move(duty_1, d1_ina1, d1_ina2, d1_pwma, duty_2, d2_ina1, d2_ina2, d2_pwma)
#         m1_enc1_val = m1_enc1.value()
#         m2_enc1_val = m2_enc1.value()
        
#         if flanco_subida(m1_enc1_val, m1_enc1_prev):
#             if m1_enc2.value():
#                 count_pulses_1 += 1
#             else:
#                 count_pulses_1 -= 1
                
        
#         if flanco_subida(m2_enc1_val, m2_enc1_prev):
#             if m2_enc2.value():
#                 count_pulses_2 += 1
#             else:
#                 count_pulses_2 -= 1
                
#         if calc_vel >= 50:
#             time_actual = time_ns()
#             delta_t = (time_actual - time_prev) / (60_000_000_000 ) # convertir a miunutos
            
#             vel_lectura_1 = count_pulses_1 / (delta_t * 345)  # 345 pulsos por vuelta
#             vel_lectura_2 = count_pulses_2 / (delta_t * 345)
            
#             # Controladores -> luwgo se pueden pasar a una funciona aparte
#             error_1 = vel_ref_1 - vel_lectura_1
#             duty_1 += Kp_1 * error_1   
#             duty_1 = max(-100, min(100, duty_1))  # Limitar entre -100 y 100    
               
#             error_2 = vel_ref_2 - vel_lectura_2
#             duty_2 += Kp_2 * error_2    
#             duty_2 = max(-100, min(100, duty_2))  # Limitar entre -100 y 100      
            
#             # Reiniciar contadores y tiempo
#             count_pulses_1 = 0
#             count_pulses_2 = 0
#             calc_vel = 0
#             time_prev = time_actual
            
        
#         m1_enc1_prev = m1_enc1_val
#         m2_enc1_prev = m2_enc1_val
#         calc_vel += 1

# def open_loop(): # Open Loop for testing
#     global vel_ref_1
#     global vel_ref_2
    
#     # Motor 1
#     duty_1 = 0          # Porcentaje de duty cycle (-100 a 100)

#     # Motor 2
#     duty_2 = 0          # Porcentaje de duty cycle (-100 a 100)

#     led.on()
    
#     while True:
#         duty_1 = vel_ref_1      # como vel = [-50, 0, 50], lo dejamos asi para que el duty este dentro del rango [-100, 100] para pruebas lazo abierto
#         duty_2 = vel_ref_2
#         move(duty_1, d1_ina1, d1_ina2, d1_pwma, duty_2, d2_ina1, d2_ina2, d2_pwma)
#         sleep_ms(10)

# ##### Wifi and conection to server #####

# async def main(ssid, password, wlan, led_wifi, ip, puerto, nombre_cliente, led_cliente):
#     uasyncio.create_task(check_wifi(ssid, password, wlan, led_wifi))
#     uasyncio.create_task(iniciar_cliente(ip, puerto, nombre_cliente, wlan, led_cliente))
    
#     while True:
#         await uasyncio.sleep_ms(10)


# #---------------------------------------------------------------------------

# ### [thread 1] Close Loop ###

# second_thread = _thread.start_new_thread(close_loop, ()) # Open or Close Loop


# ### [thread 0] Recibir Velocidades de Referencia de Base y chequear conexion a WiFi ###

# # WiFi
# ssid = 'Lucas'
# password = '1234567890'
# wlan = network.WLAN(network.STA_IF)
# # Servidor
# ip_server = '10.202.164.53'
# port = 8080
# robot_id = "FutBot_1"

# try:
#     uasyncio.run(main(ssid, password, wlan, led_verde, ip_server, port, robot_id, led_azul))
    
# finally:
#     uasyncio.new_event_loop()