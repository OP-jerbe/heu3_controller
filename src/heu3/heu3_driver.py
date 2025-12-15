"""
This module contains the driver for the Oregon Physics Heat Exchange Unit v3
"""

from threading import Lock
from typing import Optional, cast

import pyvisa
from pyvisa.resources import MessageBasedResource


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

    def __init__(
        self,
        resource_name: Optional[str] = None,
        instrument: Optional[MessageBasedResource] = None,
    ) -> None:
        self.rm = pyvisa.ResourceManager('@py')
        self.instrument: Optional[MessageBasedResource] = instrument
        if self.instrument is None and resource_name is not None:
            self.instrument = cast(
                MessageBasedResource, self.rm.open_resource(resource_name)
            )
        self.lock = Lock()

    def send_query(self, command: str) -> str:
        """
        Send a command to the instrument and read the response.

        Args:
            command (str): Command string to send to the HEUv3.

        Returns:
            str: Response from the instrument
        """
        if not self.instrument:
            raise RuntimeError(
                'Attempted to communicate with HEUv3, but no instrument is connected.'
            )

        if not command.endswith('\n'):
            command += '\n'

        with self.lock:
            try:
                response = self.instrument.query(command)
            except Exception as e:
                raise ConnectionError(f'Serial Communication Error: {e}')

            print(f'Command: "{command}"\nResponse: "{response}"')
            return response

    ####################################################################################
    ################################ Set Commands ######################################
    ####################################################################################

    def disable_echo(self) -> str:
        """
        Disable echo.

        Returns:
            str: Command string with newline.
        """
        command = 'DE'
        return self.send_query(command)  # returns "DE\n"

    def enable_echo(self) -> str:
        """
        Enable echo (default state).

        Returns:
            str: Command string with newline.
        """
        command = 'EE'
        return self.send_query(command)  # returns "EE\n"

    def enable_panel(self) -> str:
        """
        Enable the touchscreen panel (default state).

        Returns:
            str: Command string with newline.
        """
        command = 'EP'
        return self.send_query(command)  # returns "EP\n"

    def disable_panel(self) -> str:
        """
        Disable the touchscreen panel (only pump on/off buttons work).

        Returns:
            str: Command string with newline.
        """
        command = 'DP'
        return self.send_query(command)  # returns "DP\n"

    def set_pump_speed(self, set_point: int) -> str:
        """
        Set the pump speed.

        Args:
            set_point (int): Pump speed setting (0-999).

        Returns:
            str: Command string with newline.

        Raises:
            TypeError: If set_point is not an integer
            ValueError: If set_point is outside valid range.
        """
        if not isinstance(set_point, int):
            raise TypeError(
                f'Argument of type {type(set_point)} not allowed. Must be of type int.'
            )
        if set_point < 0 or set_point > 999:
            raise ValueError('Invalid speed setting. Setting must be between 0 and 999')

        speed_str = str(set_point)  # convert int to str
        speed_str = speed_str.zfill(
            3
        )  # add leading zeros so string is always 3 chars long
        command = f'SPS{speed_str}'
        return self.send_query(command)  # returns "\n"

    def enable_pumps(self) -> str:
        """
        Turn the pumps on.

        Returns:
            str: Command string with newline.
        """
        command = 'ON'
        return self.send_query(command)  # returns "\n"

    def disable_pumps(self) -> str:
        """
        Turn the pumps off.

        Returns:
            str: Command string with newline.
        """
        command = 'OFF'
        return self.send_query(command)  # returns "\n"

    def set_min_flow_interlock(self, set_point: int | float) -> str:
        """
        Set the minimum flow rate for the interlock in L/min.

        Args:
            set_point (int | float): Minimum allowable flow rate (0.5-9.99).

        Returns:
            str: Command string with newline.

        Raises:
            ValueError: If the set point is outside valid range.
        """
        if set_point < 0.5 or set_point > 10:
            raise ValueError(
                'Invalid minimum flow rate set point. Valid set point is between 0.5 and 9.99.'
            )

        if isinstance(set_point, int):
            set_point = float(set_point)

        set_point_str = f'{set_point:.2f}'
        command = f'SMINF{set_point_str}'
        return self.send_query(command)  # returns "\n"

    def select_pumps(self, pump: int) -> str:
        """
        Select which pumps to activate.

        Args:
            pump (int): 0 for both pumps, 1 for pump1, 2 for pump2.

        Returns:
            str: Command string with newline.
        """
        command = f'SPONO{pump}'
        return self.send_query(command)  # returns "{pump}\n"

    ####################################################################################
    ############################ Read State Commands ###################################
    ####################################################################################

    def read_inlet_temp(self) -> str:
        """
        Read the inlet temperature of the Galden HT-270.

        Returns:
            str: Inlet temperature of Galden in °C
        """
        command = 'RINTE'
        return self.send_query(command)

    def read_outlet_temp(self) -> str:
        """
        Read the outlet temperature of the Galden HT-270.

        Returns:
            str: Outlet temperature of Galden in °C
        """
        command = 'ROUTT'
        return self.send_query(command)

    def read_flow_rate(self) -> str:
        """
        Read the flow rate of the Galden in liters per minute.

        Returns:
            str: Flow rate of Galden as measured by internal flow meter
        """
        command = 'RFLOW'
        return self.send_query(command)

    def read_interlock_status(self) -> str:
        """
        Read the interlock status bit.

        Returns:
            str: `"1"` for on, good, `"2"` for off
        """
        command = 'RINTR'
        return self.send_query(command)

    def read_pump_status(self) -> str:
        """
        Read the status bits for the pumps.

        Returns:
            str: `"0"` for bad, `"1"` for good, `"2"` for good but manually off
        """
        command = 'RPUMP'
        return self.send_query(command)

    def read_hour_meters(self) -> str:
        """
        Read the number of hours the unit has been power on, and the number of hours each pump has been run.

        Returns:
            str: unit-on hours, pump1 hours, pump2 hours in the form `"nnnnnn nnnnnn nnnnnn"`
        """
        command = 'RHOUR'
        return self.send_query(command)

    def read_power_dissipated(self) -> str:
        """
        Read the current amount of heat being dissipated/exchanged in Watts calculated
        from flow rate and inlet/outlet temperature difference. Only valid when
        Galden HT-270 is the coolant.

        Returns:
            str: the power exchanged in the unit
        """
        command = 'RPOWR'
        return self.send_query(command)

    def read_leak_detect(self) -> str:
        """
        Read the leak detector bit.

        Returns:
            str: `"0"` for no leak, `"1"` for leak
        """
        command = 'RLEAK'
        return self.send_query(command)

    def read_datetime(self) -> str:
        """
        Read the real time clock used in logs.

        Returns:
            str: the current month, day, year, hour:minute:second
        """
        command = 'RDATI'
        return self.send_query(command)

    def read_factory_info(self) -> str:
        """
        Read the HEU build information

        Returns:
            str: serial number, protocol version, number of boot-ups, hardware
        version, software version, and compile date
        """
        command = 'RFINF'
        return self.send_query(command)

    ####################################################################################
    ########################### Read Settings Commands #################################
    ####################################################################################

    def read_pump_IO_setting(self) -> str:
        """
        Read the pumps On/Off switch state

        Returns:
            str: state of On/Off switch (`"0"` for OFF, `"1"` for ON)
        """
        command = 'RONOF'
        return self.send_query(command)

    @property
    def pump_speed(self) -> str:
        """
        GETTER: Read the pump speed setting

        Returns:
            str: pump speed setting
        """
        command = 'RPSPD'
        return self.send_query(command)

    @property
    def max_temp_interlock(self) -> str:
        """
        GETTER: Reads the maximum temperature interlock trip point setting.

        Returns:
            str: the temperature interlock set point
        """
        command = 'RMAXT'
        return self.send_query(command)

    @max_temp_interlock.setter
    def max_temp_interlock(self, value: float) -> None:
        """
        SETTER: Sets the maximum temperature interlock point.

        Args:
            value (int | float): Maximum allowable temperature (5-65 degrees C).
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
        self.send_query(command)

    @property
    def min_flow_interlock(self) -> str:
        """
        Read the flow rate interlock trip point setting.

        Returns:
            str: the flow rate interlock set point
        """
        command = 'RMINF'
        return self.send_query(command)

    @min_flow_interlock.setter
    def min_flow_interlock(self, value: float) -> None:
        """
        SETTER: Sets the minimum flow rate interlock point.

        Args:
            value (int | float): Minimum allowable flow rate in liters per minute(0.5-9.99).
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
        self.send_query(command)
