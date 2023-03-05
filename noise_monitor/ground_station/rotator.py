from __future__ import annotations

import time
import socket

from .data_structures import Position


class Rotator:
    _rotator: GenericRotator

    def __init__(
        self,
        rotator_type: str,
        netrotctl_ip: str = None,
        netrotctl_port: int = None,
        positioning_tolerance: float = None,
    ):
        rot_type = str(rotator_type).lower()
        if rot_type == "spid":
            self._rotator = SPIDRotator(
                netrotctl_ip=netrotctl_ip,
                netrotctl_port=netrotctl_port,
                positioning_tolerance=positioning_tolerance,
            )
        else:
            raise NotImplementedError(
                f"There is currently no support for {rotator_type} rotators."
            )

    def move_rotator_to_position(self, target_position: Position) -> Position:
        """This function sets the motion control of the rotator controller to move the rotator towards the given
        position. After converging into a steady rotator position, the current positional reading will be returned.

        Args:
            target_position (Position): The position (azimuth and elevation) where the rotator shall point to

        Returns (Position): The position the rotator could reach, after converging into a steady position reading.

        """
        return self._rotator.move_rotator_to_position(target_position)

    def get_position(self) -> Position:
        """This function returns the current position reading of the rotator controller.

        Returns (Position): The current position reading of the rotator controller

        """
        return self._rotator.get_position()

    def stop_motion(self):
        return self._rotator.stop_motion()

    def reset_motor_driver(self):
        return self._rotator.reset_motor_driver()


class GenericRotator:
    position: Position
    target_position: Position
    positioning_tolerance: float

    def __init__(self, positioning_tolerance: float = 0.1):
        self.positioning_tolerance = float(positioning_tolerance)

    def move_rotator_to_position(
        self, position: Position, time_interval: float = 0.5
    ) -> Position:
        # Gets rotator position and tracks motion progress.
        # If rotator position converges, it returns the measured position.
        last_position = Position(float("inf"), float("inf"))
        self.set_position(position)
        converged, count = False, 0
        while not converged:
            current_position = self.get_position()
            position_difference = abs(last_position - current_position)
            target_difference = abs(current_position - position)
            # print(
            #     f"Target-{position}, "
            #     f"Current-{current_position}, "
            #     f"Difference-{target_difference}, "
            #     f"Count:{count}"
            # )
            if (
                position_difference.azimuth < 0.5
                and position_difference.elevation < 0.5
            ):
                if (
                    target_difference.azimuth < self.positioning_tolerance
                    and target_difference.elevation < self.positioning_tolerance
                ):
                    self.stop_motion()
                    if count > 2:
                        converged = True
                        self.stop_motion()
                if count < 20:
                    count += 1
                else:
                    raise Exception("Rotator could not reach target position!")
            else:
                count = 0
            last_position = current_position
            time.sleep(time_interval)
        return self.get_position()

    @property
    def azimuth_position(self) -> float:
        return self.position.azimuth

    @property
    def elevation_position(self) -> float:
        return self.position.elevation

    def get_position(self) -> Position:
        return self.position

    def set_position(self, position: Position):
        self.target_position = position

    def stop_motion(self):
        pass

    def reset_motor_driver(self):
        pass


class SPIDRotator(GenericRotator):
    position: Position
    target_position: Position
    netrotctl_ip: str = "localhost"
    netrotctl_port: int = 4533
    positioning_tolerance: float = 0.5

    def __init__(
        self,
        netrotctl_ip: str = None,
        netrotctl_port: int = None,
        positioning_tolerance: float = None,
    ):
        if positioning_tolerance is not None:
            self.positioning_tolerance = positioning_tolerance
        super().__init__(positioning_tolerance=self.positioning_tolerance)
        if netrotctl_ip is not None:
            self.netrotctl_ip = str(netrotctl_ip)
        if netrotctl_port is not None:
            self.netrotctl_port = int(netrotctl_port)
        self.ROTCTL_ERROR = b"RPRT -1\n"
        self.ROTCTL_CONFIRM = b"RPRT 0\n"
        self.netrotctl_socket = None
        self.connect_netrotctl()
        self.position = self.get_position()
        self.target_position = self.position

    def __del__(self):
        self.disconnect_netrotctl()

    def connect_netrotctl(self):
        self.disconnect_netrotctl()
        self.netrotctl_socket = socket.create_connection(
            (self.netrotctl_ip, self.netrotctl_port)
        )

    def disconnect_netrotctl(self):
        if self.netrotctl_socket is not None:
            try:
                self.netrotctl_socket.close()
            except AttributeError:
                return

    def get_position(self) -> Position:
        pos = self._get_rotator_position()
        self.position = pos
        return pos

    def set_position(self, position: Position):
        super().set_position(position)
        self._set_rotator_position(position)

    def _send_command(self, cmd: str) -> str:
        self.netrotctl_socket.sendall(str(cmd).encode())
        data = self.netrotctl_socket.recv(64)
        return str(data, encoding="utf-8")

    def stop_motion(self):
        # Stop motion control
        self._send_command("S\n")

    def reset_motor_driver(self):
        self.stop_motion()  # Make sure rotator does not move
        self._send_command("R 2\n")  # Reset motor driver

    def _get_rotator_position(self) -> Position:
        command_message = "p\n"
        self.netrotctl_socket.sendall(command_message.encode())
        data = self.netrotctl_socket.recv(64)
        try:
            str_list = str(data, encoding="utf-8").splitlines()
            az = float(str_list[0])
            el = float(str_list[1])
            self.position = Position(az, el)
            return self.position
        except Exception:
            raise Exception(f"Unknown return value from NetRotCtl! ({data})")

    def _set_rotator_position(self, position: Position):
        command_message = f"P {position.azimuth:.3f} {position.elevation:.3f}\n"
        self.netrotctl_socket.sendall(command_message.encode())
        data = self.netrotctl_socket.recv(64)
        if data == self.ROTCTL_CONFIRM:
            return
        if data == self.ROTCTL_ERROR:
            raise Exception("ROTCTL Error")
        raise Exception(f"Unknown return value from NetRotCtl! ({data})")
