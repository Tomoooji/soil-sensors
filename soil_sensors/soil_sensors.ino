/* Soil sensors
Arduino UNO
  サーミスタ
  TDSセンサ
  土壌水分センサー
  + microSD?
*/

constexpr uint8_t pin_thrm = A0; //サーミスタ
constexpr uint8_t pin_tds = A1; //TDSセンサ
constexpr uint8_t pin_mist = A2; //土壌水分(湿度)センサ

constexpr int B_thrm = 3435; //K



#define SAMPLE_NUM 16

const int pin = 15;

int buffer[SAMPLE_NUM];
unsigned int head = 0;

void setup() {
  pinMode(pin,INPUT);
  Serial.begin(115200);
}

void loop() {
  buffer[head & (SAMPLE_NUM-1)] = analogRead(pin);
  head+=1;
  long average = 0;
  for (int val : buffer){
    average += val;
  }
  average = average / SAMPLE_NUM;
  Serial.println(average);
}
