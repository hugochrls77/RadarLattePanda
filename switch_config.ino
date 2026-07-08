// --- ARDUINO : HANDSHAKE BINAIRE ABSOLU ---
const int PINS_TX[] = {8, 9, 10};
const int PINS_RX[] = {11, 12, 13};

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 3; i++) {
    pinMode(PINS_TX[i], OUTPUT);
    pinMode(PINS_RX[i], OUTPUT);
    digitalWrite(PINS_TX[i], LOW);
    digitalWrite(PINS_RX[i], LOW);
  }
}

void loop() {
  if (Serial.available() > 0) {
    int combinaison = Serial.read(); // Lecture d'un seul octet (0 à 63)
    
    int tx = combinaison / 8;
    int rx = combinaison % 8;

    // Commutation instantanée
    digitalWrite(PINS_TX[0], (tx >> 0) & 1);
    digitalWrite(PINS_TX[1], (tx >> 1) & 1);
    digitalWrite(PINS_TX[2], (tx >> 2) & 1);

    digitalWrite(PINS_RX[0], (rx >> 0) & 1);
    digitalWrite(PINS_RX[1], (rx >> 1) & 1);
    digitalWrite(PINS_RX[2], (rx >> 2) & 1);

    delayMicroseconds(100); // 0.1 ms de stabilisation des puces HMC321

    Serial.write('K'); // Accusé de réception
  }
}
