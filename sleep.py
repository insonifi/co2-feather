import alarm
import time

def go_to_sleep(sleep_sec=1):
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_sec)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)# Write your code here :-)
