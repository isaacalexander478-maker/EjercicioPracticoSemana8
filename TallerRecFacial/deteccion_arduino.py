import time
from pathlib import Path
import cv2
import serial

URL_WOKWI = "rfc2217://localhost:4000"
VELOCIDAD = 9600
CAMARA = 0
XML = Path(__file__).resolve().parent / "haarcascade_frontalface_default.xml"

def main():
    if not hasattr(cv2, "CascadeClassifier"):
        print("Falta CascadeClassifier. Instala opencv-contrib-python.")
        return
    if not XML.is_file():
        print(f"No se encuentra el archivo XML: {XML}")
        return

    detector = cv2.CascadeClassifier(str(XML))
    if detector.empty():
        print("No se pudo cargar el XML.")
        return

    try:
        arduino = serial.serial_for_url(
    URL_WOKWI, baudrate=VELOCIDAD, timeout=0.05
        )
    except serial.SerialException as error:
        print(f"No se pudo conectar a Wokwi ({URL_WOKWI}): {error}")
        return

    camara = None
    try:
        time.sleep(2)
        arduino.write(b"R")
        camara = cv2.VideoCapture(CAMARA)
        if not camara.isOpened():
            print("No se pudo abrir la cámara.")
            return

        print("Sistema 2FA iniciado. Presiona Q para salir.")
        ultimo_envio = 0.0
        mensaje_pantalla = "ACCESO DENEGADO"
        color_pantalla = (0, 0, 255)

        while True:
            correcto, imagen = camara.read()
            if not correcto or imagen is None:
                break

            gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
            rostros = detector.detectMultiScale(
                gris, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )

            estado_camara = "A" if len(rostros) > 0 else "R"
            ahora = time.monotonic()
            if ahora - ultimo_envio >= 0.3:
                arduino.write(estado_camara.encode("ascii"))
                ultimo_envio = ahora

            while arduino.in_waiting > 0:
                linea = arduino.readline().decode("utf-8", errors="ignore").strip()
                if linea == "STATUS:PIN":
                    mensaje_pantalla = "ROSTRO OK - INGRESE PIN (#)"
                    color_pantalla = (0, 215, 255)
                    print("Rostro validado -> Esperando PIN en Keypad...")
                elif linea == "STATUS:OK":
                    mensaje_pantalla = "ACCESO CORRECTO"
                    color_pantalla = (0, 255, 0)
                    print("ACCESO CORRECTO (Rostro + PIN validados)")
                elif linea == "STATUS:PIN_ERR":
                    mensaje_pantalla = "PIN INCORRECTO - ACCESO DENEGADO"
                    color_pantalla = (0, 0, 255)
                    print("ACCESO DENEGADO (PIN incorrecto)")
                elif linea == "STATUS:DENEGADO":
                    mensaje_pantalla = "ACCESO DENEGADO"
                    color_pantalla = (0, 0, 255)
                    print("ACCESO DENEGADO")
                elif linea == "STATUS:SIN_ROSTRO":
                    print("Bloqueado: Valide su rostro antes de usar el teclado.")
                elif linea.startswith("TECLA:"):
                    digitos = int(linea.split(":")[1])
                    mensaje_pantalla = f"PIN: {'*' * digitos}"

            for x, y, ancho, alto in rostros:
                cv2.rectangle(imagen, (x, y), (x + ancho, y + alto), color_pantalla, 2)

            cv2.putText(imagen, mensaje_pantalla, (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, color_pantalla, 2)
            cv2.putText(imagen, f"Rostros detectados: {len(rostros)}", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_pantalla, 2)
            cv2.putText(imagen, "PIN: 1234 + # | Borrar: * | Salir: Q", (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            cv2.imshow("Control de Acceso Domotico 2FA", imagen)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except serial.SerialException as error:
        print(f"Error de comunicación serial: {error}")
    finally:
        try:
            if arduino.is_open:
                arduino.write(b"R")
                arduino.flush()
        except serial.SerialException:
            pass
        if camara is not None:
            camara.release()
        cv2.destroyAllWindows()
        arduino.close()
        print("Programa finalizado.")

if __name__ == "__main__":
    main()