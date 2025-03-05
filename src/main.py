import asyncio
from threading import Event
from typing import ClassVar, Mapping, Optional, Sequence, cast

from typing_extensions import Self
from viam.logging import getLogger
from viam.components.board import Board
from viam.components.sensor import Sensor
from viam.services.generic import Generic
from viam.module.module import Module
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import struct_to_dict, ValueTypes

LOGGER = getLogger("proximity-alert")

class HcSr04RgbLed(Generic, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("atacke", "proximity-alert"), "hc-sr04_rgb-led"
    )

    auto_start = True
    task = None
    event = Event()

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """This method creates a new instance of this Generic service.
        The default implementation sets the name from the `config` parameter and then calls `reconfigure`.

        Args:
            config (ComponentConfig): The configuration for this resource
            dependencies (Mapping[ResourceName, ResourceBase]): The dependencies (both implicit and explicit)

        Returns:
            Self: The resource
        """
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        """This method allows you to validate the configuration object received from the machine,
        as well as to return any implicit dependencies based on that `config`.

        Args:
            config (ComponentConfig): The configuration for this resource

        Returns:
            Sequence[str]: A list of implicit dependencies
        """
        attrs = struct_to_dict(config.attributes)
        required_dependencies = ["board", "sensor"]
        required_attributes = ["red_pin", "green_pin", "blue_pin"]
        implicit_dependencies = []
        
        for component in required_dependencies:
            if component not in attrs or not isinstance(attrs[component], str):
                raise ValueError(f"{component} is required in the configuration and must be a string")
            else:
                implicit_dependencies.append(attrs[component])

        for attribute in required_attributes:
            if attribute not in attrs or not isinstance(attrs[attribute], str):
                raise ValueError(f"{component} is required in the configuration and must be a string")

        return implicit_dependencies

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """This method allows you to dynamically update your service when it receives a new `config` object.

        Args:
            config (ComponentConfig): The new configuration
            dependencies (Mapping[ResourceName, ResourceBase]): Any dependencies (both implicit and explicit)
        """
        attrs = struct_to_dict(config.attributes)
        self.auto_start = bool(attrs.get("auto_start", self.auto_start))
        
        LOGGER.debug("Reconfiguring proximity alert...")

        # set board (raspberry pi)
        board_resource = dependencies.get(
            Board.get_resource_name(str(attrs.get("board")))
        )
        self.board = cast(Board, board_resource)

        if not isinstance(self.board, Board):
            raise Exception(f"Board '{board_resource}' not found during reconfiguration.")
        
        LOGGER.debug(f"BOARD IS SET, {self.board}")
        
        # set ultrasonic sensor
        sensor_resource = dependencies.get(
            Sensor.get_resource_name(str(attrs.get("sensor")))
        )
        self.sensor = cast(Sensor, sensor_resource)

        if not isinstance(self.sensor, Sensor):
            raise Exception(f"Sensor '{sensor_resource}' not found during reconfiguration.")
        
        LOGGER.debug(f"SENSOR IS SET, {self.sensor}")

        # set RGB LED pins
        self.red_pin_attr = str(attrs.get("red_pin", "33"))
        self.green_pin_attr = str(attrs.get("green_pin", "32"))
        self.blue_pin_attr = str(attrs.get("blue_pin", "12"))

        # set safe distance
        self.safe_distance = float(attrs.get("safe_distance", "0.2"))
        LOGGER.debug(f"SAFE DISTANCE SET, {self.safe_distance}")

        if self.auto_start:
            self.start()

        return super().reconfigure(config, dependencies)
 
    async def signal_safe(self):
        LOGGER.debug("Setting RGB to safe color...")

        await self.red_pin.set(high=False)
        await self.green_pin.set(high=True)
        await self.blue_pin.set(high=False)

    async def signal_unsafe(self):
        LOGGER.debug("Setting RGB to unsafe color...")

        await self.red_pin.set(high=True)
        await self.green_pin.set(high=False)
        await self.blue_pin.set(high=False)

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        result = {key: False for key in command.keys()}
        for name, _args in command.items():
            if name == "start":
                self.start()
                result[name] = True
            if name == "stop":
                self.stop()
                result[name] = True
        return result

    async def on_loop(self):
        is_safeColor = False

        self.red_pin = await self.board.gpio_pin_by_name(self.red_pin_attr)
        self.green_pin = await self.board.gpio_pin_by_name(self.green_pin_attr)
        self.blue_pin = await self.board.gpio_pin_by_name(self.blue_pin_attr)

        while not self.event.is_set():
            try:
                distance = (await self.sensor.get_readings())["distance"]
                
                if distance < self.safe_distance and is_safeColor:
                    LOGGER.debug(f"DISTANCE IS UNSAFE: {distance}, SETTING TO UNSAFE COLOR")    
                    await self.signal_unsafe()
                    is_safeColor = False
                elif distance >= self.safe_distance and not is_safeColor:
                    LOGGER.debug(f"DISTANCE IS SAFE: {distance}, SETTING TO SAFE COLOR")
                    await self.signal_safe()
                    is_safeColor = True
            except Exception as e:
                LOGGER.error(f"Error setting RGB LED: {e}")
        
            await asyncio.sleep(1)

    def start(self):
        if self.task is None or self.task.done():
            self.event.clear()
            self.task = asyncio.create_task(self.control_loop())

    def stop(self):
        self.event.set()
        if self.task is not None:
            self.task.cancel()

    async def control_loop(self):
        while not self.event.is_set():
            await self.on_loop()
            await asyncio.sleep(0)

    def __del__(self):
        self.stop()

    async def close(self):
        self.stop()

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())

