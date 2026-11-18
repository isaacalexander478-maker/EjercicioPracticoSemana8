#include <Arduino.h>
#include <Keypad.h>

const int LED_ROJO = 10;
const int LED_VERDE = 6;

const String PIN_CORRECTO = "1234";
String pinIngresado = "";

bool rostroDetectado = false;
bool accesoConcedido = false;

unsigned long ultimaSenalRostro = 0;
unsigned long tiempoAccesoConcedido = 0;

const unsigned long GRACIA_ROSTRO_MS = 3000;
const unsigned long DURACION_ACCESO_MS = 6000;

const byte FILAS = 4;
const byte COLUMNAS = 4;
char teclas[FILAS][COLUMNAS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

byte pinesFilas[FILAS] = {9, 8, 7, 5};
byte pinesColumnas[COLUMNAS] = {4, 3, 2, A0};

Keypad teclado = Keypad(makeKeymap(teclas), pinesFilas, pinesColumnas, FILAS, COLUMNAS);

void bloquearSistema(bool notificar) {
  accesoConcedido = false;
  pinIngresado = "";
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_ROJO, HIGH);
  if (notificar) {
    Serial.println("STATUS:DENEGADO");
  }
}

void concederAcceso() {
  accesoConcedido = true;
  tiempoAccesoConcedido = millis();
  pinIngresado = "";
  digitalWrite(LED_ROJO, LOW);
  digitalWrite(LED_VERDE, HIGH);
  Serial.println("STATUS:OK");
}

void setup() {
  pinMode(LED_ROJO, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);
  Serial.begin(9600);
  bloquearSistema(true);
}

void loop() {
  while (Serial.available() > 0) {
    char dato = Serial.read();
    if (dato == 'A') {
      if (!rostroDetectado && !accesoConcedido) {
        Serial.println("STATUS:PIN");
      }
      rostroDetectado = true;
      ultimaSenalRostro = millis();
    } else if (dato == 'R') {
      if (!accesoConcedido && (millis() - ultimaSenalRostro > GRACIA_ROSTRO_MS)) {
        if (rostroDetectado) {
          rostroDetectado = false;
          pinIngresado = "";
          Serial.println("STATUS:DENEGADO");
        }
      }
    }
  }

  if (!accesoConcedido && rostroDetectado && (millis() - ultimaSenalRostro > GRACIA_ROSTRO_MS)) {
    rostroDetectado = false;
    pinIngresado = "";
    Serial.println("STATUS:DENEGADO");
  }

  if (accesoConcedido && (millis() - tiempoAccesoConcedido > DURACION_ACCESO_MS)) {
    rostroDetectado = false;
    bloquearSistema(true);
  }

  char tecla = teclado.getKey();
  if (tecla) {
    if (!rostroDetectado && !accesoConcedido) {
      Serial.println("STATUS:SIN_ROSTRO");
      return;
    }

    if (tecla == '*') {
      rostroDetectado = false;
      bloquearSistema(true);
    } else if (tecla == '#') {
      if (pinIngresado == PIN_CORRECTO) {
        concederAcceso();
      } else {
        Serial.println("STATUS:PIN_ERR");
        pinIngresado = "";
        digitalWrite(LED_VERDE, LOW);
        digitalWrite(LED_ROJO, HIGH);
      }
    } else {
      if (pinIngresado.length() < 6) {
        pinIngresado += tecla;
        Serial.print("TECLA:");
        Serial.println(pinIngresado.length());
      }
    }
  }
}