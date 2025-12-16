"""
This module contains the driver for the Oregon Physics Heat Exchange Unit v3
"""

from threading import Lock
from typing import Optional

import serial


class HEUv3:
    """
    Class that implements the driver for the Oregon Physics Heat Exchange Unit v3.
    The driver implements the following 23 commands:

    SET COMMANDS:
    * DE: Disable Echo
    * EE: Enable Echo
    * EP: Enable touchscreen panel
    * DP: Disable touchscreen panel (only pumps on/off button will work)
    * SPSnnn: Set pump speed [nnn = `000`-`999`]
    * ON: Turn on pumps
    * OFF: Turn off pumps
    * SMAXTnn: Set maximum temperature for interlock [nn == `05`-`65`]
    * SMINFn.nn: Set minimum flow rate for interlock [n.nn == `0.50`-`9.99`]
    * SPONOn: Activate pumps [n == `0` (both pumps), `1` (pump1), `2` (pump2)]

    READ COMMANDS:
    * RINTE: Read dielectric inlet temperature in degrees C [nn.n]
    * ROUTT: Read dielectric outlet temperature in degrees C [nn.n]
    * RFLOW: Read dielectric flow rate in liters per minute [nn.nn]
    * RINTR: Read interlock output status [b == `0` (off), `1` (on/good)]
    * RPUMP: Read pump status [n,n == pump1,pump2; where `0` = bad, `1` = good, `2` = good but manually off]
    * RHOUR: Read hour meters [nnnnnn nnnnnn nnnnnn == unit-on pump1-on pump2-on]
    * RPOWR: Read exchanged heat in Watts (calculated from flow and delta-T for Galden HT-270) [nnnn]
    * RLEAK: Read leak detector status [b == `0` (no leak), `1` (leak)]
    * RDATI: Read real-time clock used in logs [text: mm,dd,YY, HH:MM:SS]
    * RFINF: Read factory information [nnnnn n nnnnn nn nn textDate == serial-number protocol-version num-of-boots hardware-version software-version compile-date]
    * RPSPD: Read pump speed setting [nnn == `000`-`999`]
    * RONOF: Read pumps on/off setting [b == `0` (off), `1` (on)]
    * RMAXT: Read maximum interlock temperature setting in degrees C [nn]
    * RMINF: Read minimum interlock flow rate setting in liters per minute [n.nn]
    * !: Ping the heat exchange unit [`WAZOO!`]
    """

    def __init__(self, com_port: Optional[str] = None) -> None:
        self._lock = Lock()
        self._com_port = com_port
        self._term_char = '\r'
        self.serial_port = None

        if self._com_port:
            self.open_connection(self._com_port)
            self.disable_echo()
            self.ping()

    def _send_query(self, query: str) -> str:
        """
        Sends a query command to the HEU, reads the response.

        Args:
            query (str): The query command string to send.
                The carriage return termination character is appended automatically.

        Returns:
            str: The decoded and stripped string response received from the instrument.
        """
        if not self.serial_port or not self.serial_port.is_open:
            raise RuntimeError(
                'Attempted to communicate with HEU, but no instrument is connected.'
            )
        if not query.endswith(self._term_char):
            query += self._term_char

        with self._lock:
            try:
                self.serial_port.reset_input_buffer()
                self.serial_port.write(query.encode())
                raw_response: str = self.serial_port.read_until(
                    self._term_char.encode()
                ).decode()
                formatted_response: str = raw_response.replace(query, '').strip()
                return formatted_response

            except Exception as e:
                print(f'Unexpected Error sending query: {e}')
                raise

    def open_connection(
        self, port: str, baudrate: int = 38400, timeout: float = 1.0
    ) -> serial.Serial | None:
        """
        Establishes a serial connection to the instrument at the specified COM port.

        Args:
            port (str): The COM port where the HEU is connected (e.g., 'COM3' or '/dev/ttyUSB0').
                The port name is automatically converted to uppercase.
            baudrate (int): The serial communication baud rate in bits per second. Defaults to 38400.
            timeout (float): The read and write timeout in seconds. Defaults to 1.0.
        """
        try:
            self.serial_port = serial.Serial(
                port=port.upper(),
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=timeout,
            )

        except Exception as e:
            print(f'Failed to make a serial connection to {port}.\n\n{str(e)}')
            self.serial_port = None

    ####################################################################################
    ################################ HEU Commands ######################################
    ####################################################################################

    def ping(self) -> str:
        """
        Sends a simple ping command to the HEU to check for communication and response.

        Returns:
            str: The response from the instrument, which is expected to be "WAZOO".
        """
        command = '!'
        return self._send_query(command)

    def disable_echo(self) -> None:
        """
        Disable echo.
        """
        command = 'DE'
        self._send_query(command)

    def enable_echo(self) -> None:
        """
        Enable echo (default state).
        """
        command = 'EE'
        self._send_query(command)

    def enable_panel(self) -> None:
        """
        Enable the touchscreen panel (default state).
        """
        command = 'EP'
        self._send_query(command)

    def disable_panel(self) -> None:
        """
        Disable the touchscreen panel (only pump on/off buttons work).
        """
        command = 'DP'
        self._send_query(command)

    def enable_pumps(self) -> None:
        """
        Turn the pumps on.
        """
        command = 'ON'
        self._send_query(command)

    def disable_pumps(self) -> None:
        """
        Turn the pumps off.

        Returns:
            str: Command string with newline.
        """
        command = 'OFF'
        self._send_query(command)

    def select_pumps(self, pump: int) -> None:
        """
        Select which pumps to activate.

        Args:
            pump (int): `0` for both pumps, `1` for pump1, `2` for pump2.
        """
        command = f'SPONO{pump}'
        self._send_query(command)

    @property
    def inlet_temp(self) -> float:
        """
        GETTER: Read the inlet temperature of the Galden HT-270.

        Returns:
            float: Inlet temperature of Galden in °C.
        """
        command = 'RINTE'
        response = self._send_query(command)
        return float(response)

    @property
    def outlet_temp(self) -> float:
        """
        GETTER: Read the outlet temperature of the Galden HT-270.

        Returns:
            float: Outlet temperature of Galden in °C.
        """
        command = 'ROUTT'
        response = self._send_query(command)
        return float(response)

    @property
    def flow_rate(self) -> float:
        """
        GETTER: Read the flow rate of the Galden in liters per minute.

        Returns:
            float: Flow rate of Galden as measured by internal flow meter in liters per minute.
        """
        command = 'RFLOW'
        response = self._send_query(command)
        return float(response)

    @property
    def is_interlocked(self) -> bool:
        """
        GETTER: Reads the interlock status bit.
        A response of `"0"` indicates the interlock circuit is open.
        A response of `"1"` indicates the interlock is satisfied.

        Returns:
            bool: `True` if the interlock is open (not satisfied). `False` if the interlock is circuit is closed (satisfied).
        """
        command = 'RINTR'
        response = self._send_query(command)
        return response == '0'

    @property
    def pump_status(self) -> tuple[int, int]:
        """
        Read the status bits for the pumps.
        response is a string of two numbers e.g. '1,1', '2,1', ...

        Returns:
            int: `0` for bad, `1` for good, `2` for good but manually off.
        """
        command = 'RPUMP'
        response: list[str] = self._send_query(command).split(',')
        pump1 = int(response[0])
        pump2 = int(response[1])
        return (pump1, pump2)

    @property
    def hour_meters(self) -> str:
        """
        GETTER: Read the number of hours the unit has been power on, and the number of hours each pump has been run.

        Returns:
            str: unit-on hours, pump1 hours, pump2 hours in the form `"nnnnnn nnnnnn nnnnnn"`.
        """
        command = 'RHOUR'
        response = self._send_query(command)
        return response

    @property
    def unit_hours(self) -> int:
        """
        GETTER: Read the number of hours that the unit has been powered on.

        Returns:
            int: Number of hours the unit has been powered on.
        """
        # The first string is the unit-on hours.
        hours = int(self.hour_meters.split(' ')[0])
        return hours

    @property
    def pump1_hours(self) -> int:
        """
        GETTER: Read the number of hours pump 1 has been running.

        Returns:
            int: Number of hours that pump 1 has been running.
        """
        # The second string is the pump1-on hours
        hours = int(self.hour_meters.split(' ')[1])
        return hours

    @property
    def pump2_hours(self) -> int:
        """
        GETTER: Read the number of hours pump 2 has been running.

        Returns:
            int: Number of hours that pump 2 has been running.
        """
        # The second string is the pump1-on hours
        hours = int(self.hour_meters.split(' ')[2])
        return hours

    @property
    def power_dissipated(self) -> int:
        """
        Read the current amount of heat being dissipated/exchanged in Watts calculated
        from flow rate and inlet/outlet temperature difference. Only valid when
        Galden HT-270 is the coolant.

        Returns:
            int: the power exchanged in the unit.
        """
        command = 'RPOWR'
        response = self._send_query(command)
        return int(response)

    @property
    def leak_detected(self) -> bool:
        """
        GETTER: Read the leak detector bit.
        response of `"0"` indicates no leak detected.
        response of `"1"` indicates there is a leak detected.

        Returns:
            bool: `True` if the leak detector sees liquid. `False` if the leak detector is dry.
        """
        command = 'RLEAK'
        response = self._send_query(command)
        return response == '1'

    @property
    def datetime(self) -> str:
        """
        GETTER: Read the real time clock used in logs.

        Returns:
            str: the current month, day, year, hour:minute:second.
        """
        command = 'RDATI'
        return self._send_query(command)

    @property
    def factory_info(self) -> str:
        """
        GETTER: Read the HEU build information.

        Returns:
            str: serial number, protocol version, number of boot-ups, hardware
        version, software version, and compile date.
        """
        command = 'RFINF'
        return self._send_query(command)

    @property
    def serial_number(self) -> str:
        """
        GETTER: Read the unit serial number.

        Returns:
            str: The unit's serial number.
        """
        # The first number in the string is the unit's serial number
        return self.factory_info.split(' ')[0]

    @property
    def protocol_version(self) -> str:
        """
        GETTER: Read the unit's protocol version.

        Returns:
            str: The units protocol version
        """
        # The second number in the string is the protocol version
        return self.factory_info.split(' ')[1]

    @property
    def boot_ups(self) -> int:
        """
        GETTER: Read the number of times the unit has booted up.

        Returns:
            int: The number of times the unit has booted up.
        """
        # The third number in the string is the number of boot ups.
        return int(self.factory_info.split(' ')[2])

    @property
    def hardware_version(self) -> str:
        """
        GETTER: Read the unit's hardware version.

        Returns:
            str: The unit's hardware version.
        """
        # The fourth number in the string is the hardware version.
        return self.factory_info.split(' ')[3]

    @property
    def sofware_version(self) -> str:
        """
        GETTER: Read the unit's software version.

        Returns:
            str: The software version installed in the HEU
        """
        # The fifth number in the string is the software version.
        return self.factory_info.split(' ')[4]

    @property
    def compile_date(self) -> str:
        """
        GETTER: Read the unit's compile date.

        Returns:
            str: The date that the software was compiled.
        """
        # The sixth (last) number in the string is the compile date.
        return self.factory_info.split(' ')[5]

    @property
    def pumps_enabled(self) -> bool:
        """
        Read the pumps On/Off switch state.
        response of `"0"` indicates pumping is disabled.
        response of `"1"` indicates pumping is enabled.

        Returns:
            bool: `True` if ON/OFF button is ON. `False` if ON/OFF button is OFF.
        """
        command = 'RONOF'
        response = self._send_query(command)
        return response == '1'

    @property
    def pump_speed(self) -> int:
        """
        GETTER: Read the pump speed setting

        Returns:
            str: The pump speed setting.
        """
        command = 'RPSPD'
        response = self._send_query(command)
        return int(response)

    @pump_speed.setter
    def pump_speed(self, value: int) -> None:
        """
        Set the pump speed.

        Args:
            value (int): Pump speed setting (0-999).

        Raises:
            TypeError: If `value` is not an integer.
            ValueError: If `value` is outside valid range (0-999).
        """
        if not isinstance(value, int):
            raise TypeError(
                f'Argument of type {type(value).__name__} not allowed. Must be of type int.'
            )
        if not 0 <= value <= 999:
            raise ValueError(
                'Invalid speed setting. Setting must be between 0 and 999.'
            )

        speed_str = str(value)
        # add leading zeros so string is always 3 chars long
        speed_str = speed_str.zfill(3)
        command = f'SPS{speed_str}'
        self._send_query(command)

    @property
    def max_temp_interlock(self) -> int:
        """
        GETTER: Reads the maximum temperature interlock trip point setting.

        Returns:
            int: the temperature interlock set point.
        """
        command = 'RMAXT'
        response = self._send_query(command)
        return int(response)

    @max_temp_interlock.setter
    def max_temp_interlock(self, value: float) -> None:
        """
        SETTER: Sets the maximum temperature interlock point.

        Args:
            value (int | float): Maximum allowable temperature (5-65 degrees C).

        Raises:
            TypeError: If `value` is not an integer or float.
            ValueError: If `value` is outside valid range (5-65).
        """
        if not isinstance(value, (int | float)):
            raise TypeError(
                f'Argument of type {type(value).__name__} not allowed. Must be of type int.'
            )

        if not 5 <= value <= 65:
            raise ValueError(
                'Invalid maximum temperature interlock set point. Valid set point is between 5-65 C.'
            )

        value = int(value)
        set_point_str = str(value)
        set_point_str = set_point_str.zfill(2)
        command = f'SMAXT{set_point_str}'
        self._send_query(command)

    @property
    def min_flow_interlock(self) -> float:
        """
        Read the flow rate interlock trip point setting.

        Returns:
            float: the flow rate interlock set point.
        """
        command = 'RMINF'
        response = self._send_query(command)
        return float(response)

    @min_flow_interlock.setter
    def min_flow_interlock(self, value: float) -> None:
        """
        SETTER: Sets the minimum flow rate interlock point.

        Args:
            value (int | float): Minimum allowable flow rate in liters per minute(0.5-9.99).

        Raises:
            TypeError: If `value` is not an integer or float.
            ValueError: If `value` is outside valid range (0.5-9.99).
        """
        if not isinstance(value, (int | float)):
            raise TypeError(
                f'Argument of type {type(value).__name__} not allowed. Must be of type int or float.'
            )
        if not 0.5 <= value < 10:
            raise ValueError(
                'Invalid minimum flow rate set point. Valid set point is between 0.5 and 9.99.'
            )

        value = float(value)
        set_point_str = f'{value:.2f}'
        command = f'SMINF{set_point_str}'
        self._send_query(command)
