#include "HX711.h"

// Load cell Declaration
#define DOUT  3
#define CLK  2
HX711 scale(DOUT, CLK);
float calibration_factor = -372990; 
float weight();
float w;

void setup() {
  Serial.begin(9600);   
  scale.set_scale();
  scale.tare(); //Reset the scale to 0
  long zero_factor = scale.read_average(); //Get a baseline reading
}

void loop(){
 w= weight();
 Serial.println(w);
}

float weight(){
         
  float measure;
  scale.set_scale(calibration_factor); //Adjust to this calibration factor
  measure=scale.get_units();
  // measure = measure*(-1);
  delay(1000);
  return(measure);
}
