
## Pump Gradual Adjustment Room Temperature for Thermia Atlas. PGART_T.

PGART is a small system that will try to reduce the electric energy consumption for a Thermia Atlas heat pump by adjusting the desired indoor temperature.

The system is tested in a Raspberry PI 2 and in an Oracle VM VirtualBox with Debian. Directory path /home/vp.

Viss dokumentation på svenska finns.

##  The system has three independent control functions. They work simultaneously.

### 1. Control according to a schedule.
A schema with instructions tells the program when to decrease/increase the temperature. One common schedule and one schedule for each weekday.

### 2. Control according to hourly rate.
The hourly rates are scraped from the web or taken from a file created by a user provided program.
#### Two run types:
* A schedule with time periods decides when a decrease based on hourly rate shall be active.
The system calculates a decrease of the temperature for the most expensive hours in the time span.
A decrease will not last for more than two consecutive hours, then there will be an hour without a decrease.

* The system decreases the temperature for a certain number of the most expensive hours. This might be several consecutive hours.

### 3. Control to compensate for the wind-chill cooling effect.
If the pump is without an indoor temperature sensor a draughty and not so well insulated house will get a lower than expected temperature when it is windy.
A new indoor temperature can be found by calculating it with the current outdoor temperature lowered by the forecasted wind-chill effect.
The system will increase the indoor temperature accordingly.
Forecasts (temperature and wind-chill) are scraped from the SMHI web or taken from a file created by user provided program.

### Additional information.
For logging purposes the system can read the indoor temperature from a Raspberry PI equipped with a temperature sensor.

The main program runs once an hour. A manual change of the temperature on the pump or via the "wheel" in Thermia-online will not be overwritten until the last scheduled run of a day.

The system accesses the heat pump via ModbusTCP and/or Thermia-online.
### Credits
Many thanks to Krisjanis Lejejs for the API https://github.com/klejejs / https://github.com/klejejs/python-thermia-online-api . The procedures for accessing Thermia-online are largely based on his work.

