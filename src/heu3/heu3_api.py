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

    def __init__(self, resource_name: Optional[str]) -> None:
        self.rm = pyvisa.ResourceManager('@py')
        self.instrument: Optional[MessageBasedResource] = None
        if resource_name is not None:
            self.instrument = cast(
                MessageBasedResource, self.rm.open_resource(resource_name)
            )
        self.lock = Lock()

    def send_query(self, command: str) -> Optional[str]:
        """
        Send a command to the instrument and read the response.

        Args:
            command (str): Command string to send to the HEUv3.

        Returns:
            Optional[str]: Response from the instrument, or None.
        """
        if not self.instrument:
            return

        if not command.endswith('\n'):
            command += '\n'

            try:
                with self.lock:
                    response = self.instrument.query(command)
                    print(f'Command: "{command}"\nResponse: "{response}"')
                    return response

            except Exception as e:
                raise ConnectionError(f'Serial Communication Error: {e}')

    ####################################################################################
    ################################ Set Commands ######################################
    ####################################################################################

    def disable_echo(self) -> Optional[str]:
        """
        Disable echo.

        Returns:
            Optional[str]: Command string with newline.
        """
        command = 'DE'
        return self.send_query(command)  # returns "DE\n"

    def enable_echo(self) -> Optional[str]:
        """
        Enable echo (default state).

        Returns:
            Optional[str]: Command string with newline.
        """
        command = 'EE'
        return self.send_query(command)  # returns "EE\n"

    def enable_panel(self) -> Optional[str]:
        """
        Enable the touchscreen panel (default state).

        Returns:
            Optional[str]: Command string with newline.
        """
        command = 'EP'
        return self.send_query(command)  # returns "EP\n"

    def disable_panel(self) -> Optional[str]:
        """
        Disable the touchscreen panel (only pump on/off buttons work).

        Returns:
            Optional[str]: Command string with newline.
        """
        command = 'DP'
        return self.send_query(command)  # returns "DP\n"

    def set_pump_speed(self, set_point: int) -> Optional[str]:
        """
        Set the pump speed.

        Args:
            set_point (int): Pump speed setting (0-999).

        Returns:
            Optional[str]: Command string with newline.

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

    def enable_pumps(self) -> Optional[str]:
        """
        Turn the pumps on.

        Returns:
            Optional[str]: Command string with newline.
        """
        command = 'ON'
        return self.send_query(command)  # returns "\n"

    def disable_pumps(self) -> Optional[str]:
        """
        Turn the pumps off.

        Returns:
            Optional[str]: Command string with newline.
        """
        command = 'OFF'
        return self.send_query(command)  # returns "\n"

    def set_max_temp_interlock(self, set_point: int) -> Optional[str]:
        """
        Set the maximum temperature for the interlock in °C.

        Args:
            set_point (int): Maximum allowable temperature (5-65).

        Returns:
            Optional[str]: Command string with newline.

        Raises:
            TypeError: If set_point is not an integer
            ValueError: If the set point is outside valid range.
        """
        if not isinstance(set_point, int):
            raise TypeError(
                f'Argument of type {type(set_point)} not allowed. Must be of type int.'
            )
        if set_point < 5 or set_point > 65:
            raise ValueError(
                'Invalid maximum temperature interlock set point. Valid set point is between 5-65.'
            )

        set_point_str = str(set_point)
        set_point_str = set_point_str.zfill(2)
        command = f'SMAXT{set_point_str}'
        return self.send_query(command)  # returns "\n"

    def set_min_flow_interlock(self, set_point: int | float) -> Optional[str]:
        """
        Set the minimum flow rate for the interlock in L/min.

        Args:
            set_point (int | float): Minimum allowable flow rate (0.5-9.99).

        Returns:
            Optional[str]: Command string with newline.

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

    def select_pumps(self, pump: int) -> Optional[str]:
        """
        Select which pumps to activate.

        Args:
            pump (int): 0 for both pumps, 1 for pump1, 2 for pump2.

        Returns:
            Optional[str]: Command string with newline.
        """
        command = f'SPONO{pump}'
        return self.send_query(command)  # returns "{pump}\n"

    ####################################################################################
    ############################### Read Commands ######################################
    ####################################################################################
