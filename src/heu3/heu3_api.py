from threading import Lock
from typing import Optional, cast

import pyvisa
from pyvisa.resources import MessageBasedResource


class HEUv3:
    """
    Provides the api for serial communication with the HEUv3.
    """

    def __init__(self, resource_name: Optional[str]) -> None:
        self.rm = pyvisa.ResourceManager('@py')
        if resource_name is not None:
            self.instrument = cast(
                MessageBasedResource, self.rm.open_resource(resource_name)
            )
        self.lock = Lock()

    def send_query(self, command: str) -> Optional[str]:
        """
        Sends a command to the instrument and reads the response

        Args:
            command[str]: string command to send to the instrument
        """
        if not command.endswith('\n'):
            command += '\n'

            try:
                with self.lock:
                    response = self.instrument.query(command)

                return response
            except Exception as e:
                raise ConnectionError(f'Serial Communication Error: {e}')

    ####################################################################################
    ################################ Set Commands ######################################
    ####################################################################################

    def enable_echo(self, enable: bool) -> Optional[str]:
        """
        Enables or disables the echo.

        Args:
            enable[bool]: True/False - Enables/Disables the command included in response
        """
        if enable:
            return self.send_query('EE')  # returns "EE\n"
        else:
            return self.send_query('DE')  # returns "DE\n"

    def enable_panel(self, enable: bool) -> Optional[str]:
        """
        Enables or disables the use of the panel. If disabled, only the on/off button works

        Args:
            enable[bool]: True/False - Enables/disables the touchscreen panel.
        """
        if enable:
            return self.send_query('EP')  # returns "EP\n"
        else:
            return self.send_query('DP')  # returns "DP\n"

    def set_pump_speed(self, speed: int) -> Optional[str]:
        """
        Sets the pumps' speed

        Args:
            speed[int]: 0-999
        """
        speed_str = str(speed)  # convert int to str
        speed_str = speed_str.zfill(
            3
        )  # add leading zeros so string is always 3 chars long
        command = f'SPS{speed_str}'
        return self.send_query(command)  # returns "\n"

    def enable_pumps(self, enable: bool) -> Optional[str]:
        """
        Turns the pumps on or off.

        Args:
            enable[bool]: True/False - Enables/disables the pumps
        """
        if enable:
            return self.send_query('ON')  # returns "\n"
        else:
            return self.send_query('OFF')  # returns "\n"

    def set_max_temp_interlock(self, set_point: int) -> Optional[str]:
        """
        Sets the maximum temperature at which the interlock will trip in degrees C.

        Args:
            set_point[int]: 5-65
        """
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
        Sets the minimum flow rate for satisfying the interlock

        Args:
            set_point[int | float]: flow rate in liters per minute
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
        Allows the selection of which pumps to use.

        Args:
            pump[int]: 0, 1, or 2. `0` selects both pumps. `1` selects pump #1, `2` selects pump #2
        """
        command = f'SPONO{pump}'
        return self.send_query(command)  # returns "{pump}\n"

    ####################################################################################
    ############################### Read Commands ######################################
    ####################################################################################
