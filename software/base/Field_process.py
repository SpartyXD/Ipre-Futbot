# Rutina de demostracion de la autonomia del robot
import cv2
import math
import time
import numpy as np

# Librerias Propias
from extras.aruco_detector2 import ArucoType
from clases import Ball, Robot, Controlable_Robot


def aruco_marker_pose_estimation(cap, detector):
    """Captura un frame y detecta los marcadores ArUco usando la nueva API
    (cv2.aruco.ArucoDetector), disponible desde OpenCV >= 4.7."""
    robots = {}
    ret, frame = cap.read()
    if not ret or frame is None:
        return None, robots  # fallo al leer la camara, salimos limpio

    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(frame_gray)
    if ids is not None:
        for i in range(len(ids)):
            if ids[i] < 10:   # Solo se consideran los marcadores con ID menor a 10
                robots[int(ids[i])] = (corners[i][0])

    return frame, robots


def detectar_color(low_color, high_color, img):
    # Convertimos la imagen a HSV
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Creamos la mascara para el color
    color_mask = cv2.inRange(img_hsv, low_color, high_color)

    # Aplicamos la mascara a la imagen original
    img_masked = cv2.bitwise_and(img, img, mask=color_mask)

    # Encontramos los contornos en la mascara
    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Lista para almacenar los centros de cada objeto detectado
    data = []

    for contour in contours:
        # Ignorar contornos muy pequenos
        if cv2.contourArea(contour) > 200:
            # Obtenemos el bounding box de cada contorno
            x, y, w, h = cv2.boundingRect(contour)
            data.append((x, y, w, h))

    # Retornamos el primer elemento de la lista de centros
    if len(data) >= 1:
        return data[0]
    else:
        return None


def detectar_pelota(frame):
    ball_pos = detectar_color((15, 50, 50), (30, 255, 255), frame)
    return ball_pos


def draw_ball(frame, info):
    x = info[0]
    y = info[1]
    w = info[2]
    h = info[3]
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 2)
    cv2.putText(frame, "Ball", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    cv2.circle(frame, (int(x + w / 2), int(y + h / 2)), 5, (0, 255, 0), -1)


def draw_robot(frame, info):
    pts = info[0]
    color = info[1]
    pos = info[2]
    top_centre = info[3]
    id = info[4]
    angle = info[5]
    tl = info[6]
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
    cv2.line(frame, pos, top_centre, color, 2)
    cv2.putText(frame, f"ID: {id}, {angle} deg", (int(tl[0]), int(tl[1]) - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def Get_Field_Data(robots: dict, ball: Ball):

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir la camara (indice 0). Revisa la conexion/permisos.")

    aruco_dict = cv2.aruco.getPredefinedDictionary(ArucoType["DICT_4X4_1000"])
    aruco_params = cv2.aruco.DetectorParameters()
    # Nueva API (OpenCV >= 4.7): el detector se crea una sola vez y se reutiliza.
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

    try:
        while True:
            # Always get the latest frame and detected markers
            frame, robots_pos = aruco_marker_pose_estimation(cap, detector)
            if frame is None:
                continue

            ball_pos = detectar_pelota(frame)

            for id in robots_pos:
                if id in robots:
                    r = robots[id]
                    r.update_position(robots_pos[id])
                    # r.draw(frame)
                    draw_robot(frame, r.get_draw_info())
                    robots[id] = r

            if ball_pos is not None:
                ball.update_position(ball_pos)
                draw_ball(frame, ball.get_draw_info())
                # ball.draw(frame)

            # cv2.putText(frame, f"STATE: {STATE}", (int(frame.shape[0]/2), 30),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)

            cv2.imshow('ArUco Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break  # antes era 'pass': nunca salia del loop al presionar 'q'
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    robots_list = {
        0: Controlable_Robot(0, True),
        1: Robot(1, False)
    }

    ball = Ball()

    Get_Field_Data(robots_list, ball)