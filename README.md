# `proximity-alert` module 

This module implements the [`rdk:service:generic` API](https://docs.viam.com/appendix/apis/services/generic/) to use with the proximity alert workshop.

With this model, you can automatically start sensing distances with the ultrasonic sensor and turn an RGB LED red or green if it passes a specified "safe" threshold.

## Requirements
This module assumes you have a Viam machine configured with a board component that is connected to an ultrasonic sensor and an RGB LED. (See the proximity-alert workshop to get started)

## Model atacke:proximity-alert:hc-sr04_rgb-led
Using the ultrasonic sensor's readings and the configured `safe_distance`, the proximity alert will change the color of the RGB LED as follows:

| Detected distance          | Meaning   | RGB LED Color | 
|---------------|--------|-----------|
| Greater than or equal to `safe_distance` (default is `0.2`) | Object is within a safe distance or farther  | Green | 
| Less than `safe_distance` (default is `0.2`) | Object is too close, surpassing the safe distance threshold | Red | 

If you wish to customize these colors or write your own logic, you can [create your own module](https://docs.viam.com/operate/get-started/other-hardware/hello-world-module/) using this repository as a starting point.

### Configuration
The following attribute template can be used to configure this model:

```json
{
  "board": <string>,
  "sensor": <string>,
  "red_pin": <string>,
  "green_pin": <string>,
  "blue_pin": <string>,
  "safe_distance": <float>
}
```

#### Attributes

The following attributes are available for this model:

| Name          | Type   | Inclusion | Description                |
|---------------|--------|-----------|----------------------------|
| `board` | string  | Required | The name of the board component (which is the same as the Raspberry Pi board in the Viam app). This will be used to control the GPIO pins for the ultrasonic sensor and the RGB LED. |
| `sensor` | string | Required | The name of the HC-SR04 ultrasonic sensor component in the Viam app. |
| `red_pin` | string | Required | A string representing the physical pin on your board connected to the red lead of a common cathode RGB LED. The string must contain only digits, such as "33" |
| `green_pin` | string | Required | A string representing the physical pin on your board connected to the green lead of a common cathode RGB LED. The string must contain only digits, such as "32" |
| `blue_pin` | string | Required | A string representing the physical pin on your board connected to the blue lead of a common cathode RGB LED. The string must contain only digits, such as "12" |
| `safe_distance` | float | Optional | The designated threshold that determines when to turn the RGB LED a safe (green) or unsafe (red) color. If an object is detected to be at or greater than this distance, it is considered a "safe" distance and will light accordingly. If an object is detected to be less than this distance, it is considered an "unsafe" distance and will light accordingly. Default is  `0.2` |

#### Example Configuration

```json
{
  "board": "board-1",
  "sensor": "sensor-x",
  "red_pin": "33",
  "green_pin": "32",
  "blue_pin": "12",
  "safe_distance": "0.3"
}
```

