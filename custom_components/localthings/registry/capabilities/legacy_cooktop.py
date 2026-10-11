"""Extra read-only options for the TP6X and existing options-array cooktops.

NZ36K7570R reports this surface over HTTPS. Timer units, flex-coil encoding
and physical burner positions are unverified; retain raw values and slot IDs.
"""

import dataclasses

from ..entities import BinarySensorDesc, SensorDesc
from . import cooktop, dishwasher

_OPTIONS = "x.com.samsung.da.options"


def _value(options, prefix):
    return cooktop._option_value(options, prefix)


def _present(prefix):
    return lambda rep, resources: _value(rep.get(_OPTIONS), prefix) is not None


def _on_off(value):
    return {"On": True, "Off": False}.get(value)


def _option_sensor(key, prefix, *, value_fn=None, **kwargs):
    def read(options):
        value = _value(options, prefix)
        return value_fn(value) if value_fn else value

    return SensorDesc(
        key=key,
        field=_OPTIONS,
        value_fn=read,
        exists_fn=_present(prefix),
        **kwargs,
    )


def _option_binary(key, prefix, **kwargs):
    return BinarySensorDesc(
        key=key,
        field=_OPTIONS,
        value_fn=lambda options: _on_off(_value(options, prefix)),
        exists_fn=_present(prefix),
        **kwargs,
    )


MODE = dataclasses.replace(
    cooktop.COOKTOP_MODE,
    entities=(
        *cooktop.COOKTOP_MODE.entities,
        _option_sensor("cooktop_model", "DeviceType", entity_category="diagnostic"),
        _option_binary("cooktop_sync_flex", "SyncFlex", icon="mdi:vector-link"),
        _option_sensor("cooktop_flex_coil", "FlexCoil", entity_category="diagnostic"),
        _option_binary("cooktop_paused", "Pause", icon="mdi:pause"),
        _option_sensor(
            "main_timer_set",
            "MainTimerSet",
            value_fn=cooktop._int_or_none,
            icon="mdi:timer-cog-outline",
        ),
        *(
            _option_sensor(
                f"burner_{slot}_pan_size",
                f"PanSize{slot}",
                translation_key="burner_pan_size",
                translation_placeholders={"number": str(slot)},
                icon="mdi:circle-double",
            )
            for slot in cooktop._SUPPORTED_OPERATION_SLOTS
        ),
    ),
)

# Reuse the shared diagnosis status without offering an untested start command.
DIAGNOSIS = dataclasses.replace(
    dishwasher.DIAGNOSIS,
    entities=tuple(e for e in dishwasher.DIAGNOSIS.entities if isinstance(e, SensorDesc)),
)
