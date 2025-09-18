from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.enums import Ability, Weather
from src.battle_factory.enums.status import Status1


def _apply_heal(mon: BattlePokemon, amount: int) -> int:
    """Apply healing to a battler and return amount restored.

    Source: pokeemerald/src/battle_script_commands.c (Cmd_manipulatedamage for
    healing families) and HP updates in Cmd_datahpupdate.
    """
    before = mon.hp
    mon.hp = min(mon.maxHP, mon.hp + amount)
    return mon.hp - before


def primary_restore_half(battle_state: BattleState) -> None:
    """Recover/Soft-Boiled/Milk Drink: heal 1/2 of max HP.

    Source: data/battle_scripts_1.s (BattleScript_EffectRecover family)
    and handling in battle_script_commands.c
    """
    user_id = battle_state.battler_attacker
    mon = battle_state.battlers[user_id]
    if mon is None or mon.hp <= 0:
        return
    heal = max(1, mon.maxHP // 2)
    restored = _apply_heal(mon, heal)
    battle_state.script_damage = -restored


def primary_rest(battle_state: BattleState) -> None:
    """Rest: fully heal HP, cure status, then sleep for 2 turns (Gen 3).

    Source: data/battle_scripts_1.s (BattleScript_EffectRest)
    and related command handling.
    """
    user_id = battle_state.battler_attacker
    mon = battle_state.battlers[user_id]
    if mon is None or mon.hp <= 0:
        return
    # Insomnia/Vital Spirit prevent sleep -> Rest fails
    if mon.ability in (Ability.INSOMNIA, Ability.VITAL_SPIRIT):
        return
    # If already at full HP, Rest still sets sleep and cures status in-game; keep faithful heal-to-full
    heal = max(0, mon.maxHP - mon.hp)
    restored = _apply_heal(mon, heal)
    # Cure all non-volatile major statuses and set sleep 2 turns
    mon.status1 = Status1.create_sleep(2)
    battle_state.script_damage = -restored


def primary_weather_heal(battle_state: BattleState) -> None:
    """Morning Sun / Synthesis / Moonlight: heal amount varies by weather.

    Gen 3: 1/2 normally; 2/3 in sun; 1/4 in rain/sand/hail. Cloud Nine/Air Lock neutralize to normal.

    Source: data/battle_scripts_1.s (BattleScript_EffectMorningSun /
    BattleScript_EffectSynthesis / BattleScript_EffectMoonlight)
    """
    user_id = battle_state.battler_attacker
    mon = battle_state.battlers[user_id]
    if mon is None or mon.hp <= 0:
        return

    # Determine heal fraction
    fraction_num, fraction_den = 1, 2  # default 1/2

    # If weather effects are nullified, keep default 1/2
    if not battle_state.are_weather_effects_nullified():
        if battle_state.weather == Weather.SUN:
            fraction_num, fraction_den = 2, 3
        elif battle_state.weather in (Weather.RAIN, Weather.SANDSTORM, Weather.HAIL):
            fraction_num, fraction_den = 1, 4

    heal = max(1, (mon.maxHP * fraction_num) // fraction_den)
    restored = _apply_heal(mon, heal)
    battle_state.script_damage = -restored
