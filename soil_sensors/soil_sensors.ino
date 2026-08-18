/* Soil sensors
Arduino UNO
  サーミスタ
  TDSセンサ
  土壌水分センサー
  + microSD?
*/
#include "Median.h"

enum PIN_NUM {
  PIN_THERMO = 33,
  PIN_TDS = 32,
  PIN_MOIST1 = 34,
  PIN_MOIST2 = 35
};

namespace THERMO {
const float B_COEFFICIENT = 3435.0;        // B定数
const float NOMINAL_RESISTANCE = 10000.0;  // 25℃での基準抵抗値 (10kΩ)
const float NOMINAL_TEMPERATURE = 25.0;    // 基準温度 (25℃)
const float SERIES_RESISTANCE = 10000.0;   // 分圧用固定抵抗 (10kΩ)
const float ADC_MAX_VALUE = 4095.0;        // 12bit ADCの最大カウント値
int buffer[100];
Median<int> median{buffer,100};

};
//Median_create(int,100,thermo_med};

namespace TDS {
const float VREF = 3.3;
const int SCOUNT = 30;
const float tds2ec = 2;
int buffer[100];
Median<int> median{buffer,100};
};
//Median_create(int,100,tds_med};

float calc_temperature(int adcValue) {
  float resistance = THERMO::SERIES_RESISTANCE * ((THERMO::ADC_MAX_VALUE / (float)adcValue) - 1.0);
  // B定数に基づいた温度計算（ステインハート・ハートの簡易式）
  float steinhart;
  steinhart = resistance / THERMO::NOMINAL_RESISTANCE;        // (R/Ro)
  steinhart = log(steinhart);                                 // ln(R/Ro)
  steinhart /= THERMO::B_COEFFICIENT;                         // 1/B * ln(R/Ro)
  steinhart += 1.0 / (THERMO::NOMINAL_TEMPERATURE + 273.15);  // + 1/To
  steinhart = 1.0 / steinhart;                                // 逆数をとってケルビン温度(K)に変換
  float temperatureC = steinhart - 273.15;                    // 摂氏(℃)に変換
  return temperatureC;
}


float calc_tds(int adcvalue, float temperature) {
  float Voltage = adcvalue * (float)TDS::VREF / 4096.0;

  //temperature compensation formula: fFinalResult(25^C) = fFinalResult(current)/(1.0+0.02*(fTP-25.0));
  float compensationCoefficient = 1.0 + 0.02 * (temperature - 25.0);
  //temperature compensation
  float compensationVoltage = Voltage / compensationCoefficient;

  //convert voltage value to tds value
  float tdsValue = (133.42 * compensationVoltage * compensationVoltage * compensationVoltage - 255.86 * compensationVoltage * compensationVoltage + 857.39 * compensationVoltage) * 0.5;
  return tdsValue;
}

void setup() {
  Serial.begin(115200);
  THERMO::median.init();
  TDS::median.init();
}

void loop() {
  float temp = calc_temperature(THERMO::median.calc(analogRead(PIN_THERMO)));
  float ec = calc_tds(TDS::median.calc(analogRead(PIN_TDS)), temp) * TDS::tds2ec;
  Serial.print(temp,2);
  Serial.print(",");
  Serial.print(ec,2);
  Serial.println();
  delay(10);
}