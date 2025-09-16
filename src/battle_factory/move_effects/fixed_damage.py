from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.enums import Move


def set_fixed_damage(battle_state: BattleState, amount: int) -> None:
    """Set fixed damage amount for script handling.

    Used by fixed-damage effects to place the computed value into
    gBattleMoveDamage/script_damage for subsequent HP update.

    Source: pokeemerald/src/battle_script_commands.c (Cmd_manipulatedamage cases)
    """
    battle_state.battle_move_damage = max(0, amount)
    battle_state.script_damage = battle_state.battle_move_damage


def effect_dragon_rage(battle_state: BattleState) -> None:
    """Dragon Rage: deal exactly 40 damage.

    Source: data/battle_scripts_1.s (BattleScript_EffectDragonRage)
    """
    set_fixed_damage(battle_state, 40)


def effect_sonic_boom(battle_state: BattleState) -> None:
    """Sonic Boom: deal exactly 20 damage.

    Source: data/battle_scripts_1.s (BattleScript_EffectSonicBoom)
    """
    set_fixed_damage(battle_state, 20)


def effect_level_damage(battle_state: BattleState) -> None:
    """Night Shade / Seismic Toss: damage equals user's level.

    Source: data/battle_scripts_1.s (BattleScript_EffectLevelDamage)
    """
    attacker = battle_state.battlers[battle_state.battler_attacker]
    set_fixed_damage(battle_state, attacker.level if attacker else 0)


def effect_super_fang(battle_state: BattleState) -> None:
    """Super Fang: halve target's current HP (min 1 if target has HP).

    Source: data/battle_scripts_1.s (BattleScript_EffectSuperFang)
    """
    target = battle_state.battlers[battle_state.battler_target]
    if not target or target.hp <= 0:
        set_fixed_damage(battle_state, 0)
        return
    dmg = target.hp // 2
    if dmg < 1:
        dmg = 1
    set_fixed_damage(battle_state, dmg)


def effect_endeavor(battle_state: BattleState) -> None:
    """Endeavor: set damage so target HP becomes equal to user's HP.

    No effect if user's HP >= target's HP.
    Source: data/battle_scripts_1.s (BattleScript_EffectEndeavor)
    """
    attacker = battle_state.battlers[battle_state.battler_attacker]
    target = battle_state.battlers[battle_state.battler_target]
    if not attacker or not target:
        set_fixed_damage(battle_state, 0)
        return
    if attacker.hp >= target.hp:
        set_fixed_damage(battle_state, 0)
        return
    dmg = target.hp - attacker.hp
    set_fixed_damage(battle_state, dmg)
