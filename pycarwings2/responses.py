import logging
from datetime import date, timedelta, datetime

log = logging.getLogger("pycarwings2")

CONNECTED_VALUE_MAP = {
	'CONNECTED': True,
	'NOT_CONNECTED'  : False
}

def _time_remaining(t):
	minutes = float(0)
	if t:
		if t["hours"]:
			minutes = float(60*t["hours"])
		if t["minutes"]:
			minutes += t["minutes"]
	return minutes


class CarwingsResponse:
	def _set_cruising_ranges(self, status):
		self.cruising_range_ac_off_km = float(status["cruisingRangeAcOff"]) / 1000
		self.cruising_range_ac_on_km = float(status["cruisingRangeAcOn"]) / 1000

	def _set_timestamp(self, status):
		self.timestamp = datetime.strptime(status["timeStamp"], "%Y-%m-%d %H:%M:%S") # "2016-01-02 17:17:38"

	"""
	example JSON response to login:

	{
		"status":200,
		"message":"success",
		"sessionId":"12345678-1234-1234-1234-1234567890",
		"VehicleInfoList": {
			"VehicleInfo": [
				{
					"charger20066":"false",
					"nickname":"LEAF",
					"telematicsEnabled":"true",
					"vin":"1ABCDEFG2HIJKLM3N"
				}
			],
			"vehicleInfo": [
				{
					"charger20066":"false",
					"nickname":"LEAF",
					"telematicsEnabled":"true",
					"vin":"1ABCDEFG2HIJKLM3N"
				}
			]
		},
		"vehicle": {
			"profile": {
				"vin":"1ABCDEFG2HIJKLM3N",
				"gdcUserId":"FG12345678",
				"gdcPassword":"password",
				"encAuthToken":"ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ",
				"dcmId":"123456789012",
				"nickname":"Alpha124",
				"status":"ACCEPTED",
				"statusDate": "Aug 15, 2015 07:00 PM"
			}
		},
		"EncAuthToken":"ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ",
		"CustomerInfo": {
			"UserId":"AB12345678",
			"Language":"en-US",
			"Timezone":"America\/New_York",
			"RegionCode":"NNA",
			"OwnerId":"1234567890",
			"Nickname":"Bravo456",
			"Country":"US",
			"VehicleImage":"\/content\/language\/default\/images\/img\/ph_car.jpg",
			"UserVehicleBoundDurationSec":"999971200",
			"VehicleInfo": {
				"VIN":"1ABCDEFG2HIJKLM3N",
				"DCMID":"201212345678",
				"SIMID":"12345678901234567890",
				"NAVIID":"1234567890",
				"EncryptedNAVIID":"1234567890ABCDEFGHIJKLMNOP",
				"MSN":"123456789012345",
				"LastVehicleLoginTime":"",
				"UserVehicleBoundTime":"2015-08-17T14:16:32Z",
				"LastDCMUseTime":""
			}
		},
		"UserInfoRevisionNo":"1"
	}
	"""
class CarwingsLoginResponse(CarwingsResponse):
	def __init__(self, response):
		profile = response["vehicle"]["profile"]
		self.gdc_user_id = profile["gdcUserId"]
		self.dcm_id = profile["dcmId"]
		self.vin = profile["vin"]

		self.nickname = response["VehicleInfoList"]["vehicleInfo"][0]["nickname"]

		customer_info = response["CustomerInfo"]
		self.tz = customer_info["Timezone"]
		self.language = customer_info["Language"]
		self.user_vehicle_bound_time = customer_info["VehicleInfo"]["UserVehicleBoundTime"]

		self.leafs = [ {
			"vin": self.vin,
			"nickname": self.nickname,
			"bound_time": self.user_vehicle_bound_time
		} ]



"""
	{
		"status": 200,
		"message": "success",
		"responseFlag": "1",
		"operationResult": "START",
		"timeStamp": "2016-01-02 17:17:38",
		"cruisingRangeAcOn": "115328.0",
		"cruisingRangeAcOff": "117024.0",
		"currentChargeLevel": "0",
		"chargeMode": "220V",
		"pluginState": "CONNECTED",
		"charging": "YES",
		"chargeStatus": "CT",
		"batteryDegradation": "10",
		"batteryCapacity": "12",
		"timeRequiredToFull": {
			"hours": "",
			"minutes": ""
		},
		"timeRequiredToFull200": {
			"hours": "",
			"minutes": ""
		},
		"timeRequiredToFull200_6kW": {
			"hours": "",
			"minutes": ""
		}
	}
"""
class CarwingsBatteryStatusResponse(CarwingsResponse):
	def __init__(self, status):
		self._set_timestamp(status)
		self._set_cruising_ranges(status)

		self.battery_capacity = status["batteryCapacity"]
		self.battery_degradation = status["batteryDegradation"]

		try:
			self.is_connected = CONNECTED_VALUE_MAP[status["pluginState"]]
		except KeyError:
			log.error(u"Unknown connected state: '%s'" % status["pluginState"])
			self.is_connected = True # probably

		self.charging_status = status["chargeMode"]

		self.is_charging = ("YES" == status["charging"])

		self.time_to_full_trickle = timedelta(minutes=_time_remaining(status["timeRequiredToFull"]))
		self.time_to_full_l2 = timedelta(minutes=_time_remaining(status["timeRequiredToFull200"]))
		self.time_to_full_l2_6kw = timedelta(minutes=_time_remaining(status["timeRequiredToFull200_6kW"]))

		self.battery_percent = 100 * float(status["batteryDegradation"]) / float(status["batteryCapacity"])

"""
	{
		"status":200,
		"message":"success",
		"responseFlag":"1",
		"operationResult":"START_BATTERY",
		"acContinueTime":"15",
		"cruisingRangeAcOn":"106400.0",
		"cruisingRangeAcOff":"107920.0",
		"timeStamp":"2016-02-05 12:59:46",
		"hvacStatus":"ON"
	}
"""
class CarwingsStartClimateControlResponse(CarwingsResponse):
	def __init__(self, status):
		self._set_timestamp(status)
		self._set_cruising_ranges(status)

		self.operation_result = status["operationResult"] # e.g. "START_BATTERY", ...?
		self.ac_continue_time = timedelta(minutes=float(status["acContinueTime"]))
		self.hvac_status = status["hvacStatus"]  # "ON" or "OFF"
		self.is_hvac_running = ("ON" == self.hvac_status)
"""
	{
		"status":200,
		"message":"success",
		"responseFlag":"1",
		"operationResult":"START",
		"timeStamp":"2016-02-09 03:32:51",
		"hvacStatus":"OFF"
	}
"""
class CarwingsStopClimateControlResponse(CarwingsResponse):
	def __init__(self, status):
		self._set_timestamp(status)
		self.hvac_status = status["hvacStatus"]  # "ON" or "OFF"
		self.is_hvac_running = ("ON" == self.hvac_status)
"""
	{
		"status":200,
		"message":"success",
		"LastScheduledTime":"Feb  9, 2016 05:39 PM",
		"ExecuteTime":"2016-02-10 01:00:00",
		"DisplayExecuteTime":"Feb  9, 2016 08:00 PM",
		"TargetDate":"2016\/02\/10 01:00"
	}
"""
class CarwingsClimateControlScheduleResponse(CarwingsResponse):
	def __init__(self, status):
		self.display_execute_time = status["DisplayExecuteTime"] # displayable, timezone-adjusted
		self.execute_time = datetime.strptime(status["ExecuteTime"]+" UTC", "%Y-%m-%d %H:%M:%S %Z") # GMT
		self.display_last_scheduled_time = status["LastScheduledTime"] # displayable, timezone-adjusted
		self.last_scheduled_time = datetime.strptime(status["LastScheduledTime"], "%b %d, %Y %I:%M %p")
		# unknown purpose; don't surface to avoid confusion
		# self.target_date = status["TargetDate"]
"""
	{
		"status":200,
		"message":"success",
		"DriveAnalysisBasicScreenResponsePersonalData": {
			"DateSummary":{
				"TargetDate":"2016-02-03",
				"ElectricMileage":"4.4",
				"ElectricMileageLevel":"3",
				"PowerConsumptMoter":"295.2",
				"PowerConsumptMoterLevel":"4",
				"PowerConsumptMinus":"84.8",
				"PowerConsumptMinusLevel":"3",
				"PowerConsumptAUX":"17.1",
				"PowerConsumptAUXLevel":"5",
				"DisplayDate":"Feb  3, 16"
			},
			"ElectricCostScale":"miles\/kWh"
		},
		"AdviceList":{
			"Advice":{
				"title":"World Number of Trips Rankings (last week):",
				"body":"The highest number of trips driven was 130 by a driver located in Japan."
			}
		}
	}
"""
class CarwingsDrivingAnalysisResponse(CarwingsResponse):
	def __init__(self, status):
			summary = status["DriveAnalysisBasicScreenResponsePersonalData"]["DateSummary"]

			# avg energy economy, in units of 'electric_cost_scale' (e.g. miles/kWh)
			self.electric_mileage = summary["ElectricMileage"]
			# rating for above, scale of 1-5
			self.electric_mileage_level = summary["ElectricMileageLevel"]

			# "acceleration performance": "electricity used for motor activation over 1km", Watt-Hours
			self.power_consumption_moter = summary["PowerConsumptMoter"] # ???
			# rating for above, scale of 1-5
			self.power_consumption_moter_level = summary["PowerConsumptMoterLevel"] # ???

			# Watt-Hours generated by braking
			self.power_consumption_minus = summary["PowerConsumptMinus"] # ???
			# rating for above, scale of 1-5
			self.power_consumption_minus_level = summary["PowerConsumptMinusLevel"] # ???

			# Electricity used by aux devices, Watt-Hours
			self.power_consumption_aux = summary["PowerConsumptAUX"] # ???
			# rating for above, scale of 1-5
			self.power_consumption_aux_level = summary["PowerConsumptAUXLevel"] # ???

			self.display_date = summary["DisplayDate"] # "Feb  3, 16"


			self.electric_cost_scale = status["DriveAnalysisBasicScreenResponsePersonalData"]["ElectricCostScale"]

			self.advice = [ status["AdviceList"]["Advice"] ] # will contain "title" and "body"

"""
	{
		"status":200,
		"message":"success",
		"BatteryStatusRecords":{
			"OperationResult":"START",
			"OperationDateAndTime":"Feb  9, 2016 11:09 PM",
			"BatteryStatus":{
				"BatteryChargingStatus":"NOT_CHARGING",
				"BatteryCapacity":"12",
				"BatteryRemainingAmount":"3",
				"BatteryRemainingAmountWH":"",
				"BatteryRemainingAmountkWH":""
			},
			"PluginState":"NOT_CONNECTED",
			"CruisingRangeAcOn":"39192.0",
			"CruisingRangeAcOff":"39744.0",
			"TimeRequiredToFull":{              # 120V
				"HourRequiredToFull":"18",
				"MinutesRequiredToFull":"30"
			},
			"TimeRequiredToFull200":{           # 240V, 3kW
				"HourRequiredToFull":"6",
				"MinutesRequiredToFull":"0"
			},
			"TimeRequiredToFull200_6kW":{       # 240V, 6kW
				"HourRequiredToFull":"4",
				"MinutesRequiredToFull":"0"
			},
			"NotificationDateAndTime":"2016\/02\/10 04:10",
			"TargetDate":"2016\/02\/10 04:09"
		}
	}
"""
# TODO: fill this in
class CarwingsLatestBatteryStatusResponse(CarwingsResponse):
	def __init__(self, status):
		pass

class CarwingsElectricRateSimulationResponse(CarwingsResponse):
	def __init__(self, status):
		r = status["PriceSimulatorDetailInfoResponsePersonalData"]
		t = r["PriceSimulatorTotalInfo"]

		self.month = r["DisplayMonth"] # e.g. "Feb/2016"

		self.total_number_of_trips = t["TotalNumberOfTrips"]
		self.total_power_consumption = t["TotalPowerConsumptTotal"] # in kWh
		self.total_acceleration_power_consumption = t["TotalPowerConsumptMoter"] # in kWh
		self.total_power_regenerated_in_braking = t["TotalPowerConsumptMinus"] # in kWh
		self.total_travel_distance_km = float(t["TotalTravelDistance"]) / 1000 # assumed to be in meters?

		self.total_electric_mileage = t["TotalElectricMileage"] # ???
		self.total_co2_reduction = t["TotalCO2Reductiont"] # ??? (yep, extra 't' at the end)

		self.electricity_rate = r["ElectricPrice"]
		self.electric_bill = r["ElectricBill"]
		self.electric_cost_scale = r["ElectricCostScale"] # e.g. "miles/kWh"