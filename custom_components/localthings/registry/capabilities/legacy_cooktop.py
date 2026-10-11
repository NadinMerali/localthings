"""Extra read-only options for the TP6X and existing options-array cooktops.

NZ36K7570R reports this surface over HTTPS. Only its first two burner labels
are confirmed; timer units and flex-coil encoding remain raw and unverified.
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


def _nz36k7570r(rep, resources):
    return (
        resources.get("/information/vs/0", {}).get("x.com.samsung.da.description") == "TP6X_CT_16K"
        and _value(rep.get(_OPTIONS), "DeviceType") == "NV9300K-/AA2"
    )


MODE = dataclasses.replace(
    cooktop.COOKTOP_MODE,
    match_fn=lambda rep, resources: not _nz36k7570r(rep, resources),
    entities=(
        *cooktop.COOKTOP_MODE.entities,
        _option_sensor("cooktop_model", "DeviceType", entity_category="diagnostic"),
        _option_binary("cooktop_sync_control", "SyncFlex", icon="mdi:vector-link"),
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


def _tp6x_entities():
    # Slots 0 and 1 are confirmed as burners 1 and 2 on the NZ36K7570R.
    # Restrict this mapping to its five reported slots; reads retain raw IDs.
    numbers = {"0": "1", "1": "2", "3": "3", "4": "4", "5": "5"}
    for entity in MODE.entities:
        if not entity.key.startswith("burner_"):
            yield entity
            continue
        slot = entity.key.split("_")[1]
        if (number := numbers.get(slot)) is not None:
            yield dataclasses.replace(
                entity,
                key=entity.key.replace(f"burner_{slot}_", f"burner_{number}_", 1),
                translation_placeholders={"number": number},
            )


TP6X_MODE = dataclasses.replace(
    MODE,
    match_fn=_nz36k7570r,
    entities=tuple(_tp6x_entities()),
)

# Reuse the shared diagnosis status without offering an untested start command.
DIAGNOSIS = dataclasses.replace(
    dishwasher.DIAGNOSIS,
    entities=tuple(e for e in dishwasher.DIAGNOSIS.entities if isinstance(e, SensorDesc)),
)
