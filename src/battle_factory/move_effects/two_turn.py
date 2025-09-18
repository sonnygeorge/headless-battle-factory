from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.enums import Status2, Weather, SemiInvulnState
from src.battle_factory.damage_calculator import DamageCalculator
from src.battle_factory.data.moves import get_move_type
from src.battle_factory.type_effectiveness import TypeEffectiveness
from src.battle_factory.enums import Move
from src.battle_factory.utils import rng


def start_charging(battle_state: BattleState) -> None:
    """Mark user as charging for two-turn moves.

    Source: pokeemerald/data/battle_scripts_1.s (BattleScript_EffectTwoTurns)
            and pokeemerald/src/battle_script_commands.c
    """
    attacker_id = battle_state.battler_attacker
    # Mark charging turn in ProtectStruct
    battle_state.protect_structs[attacker_id].chargingTurn = True


def clear_charging(battle_state: BattleState) -> None:
    """Clear charging flag after the second turn resolves.

    Source: same as start_charging
    """
    attacker_id = battle_state.battler_attacker
    battle_state.protect_structs[attacker_id].chargingTurn = False


def set_semi_invulnerable(battle_state: BattleState, state: SemiInvulnState, value: bool) -> None:
    """Set the appropriate semi-invulnerability status3 flag for Fly/Dig/Dive.

    Source: BattleScript_EffectSemiInvulnerable and associated checks.
    """
    idx = battle_state.battler_attacker
    if state == SemiInvulnState.AIR:
        battle_state.status3_on_air[idx] = value
    elif state == SemiInvulnState.UNDERGROUND:
        battle_state.status3_underground[idx] = value
    elif state == SemiInvulnState.UNDERWATER:
        battle_state.status3_underwater[idx] = value


def resolve_two_turn_damage(battle_state: BattleState) -> None:
    """Compute and apply damage like a normal hit for the current move.

    Mirrors the second-turn resolution for Razor Wind/Sky Attack/Solar Beam
    and semi-invulnerable moves.

    Sources: data/battle_scripts_1.s and battle_script_commands.c
    """
    attacker_id = battle_state.battler_attacker
    target_id = battle_state.battler_target
    attacker = battle_state.battlers[attacker_id]
    defender = battle_state.battlers[target_id]
    if attacker is None or defender is None or defender.hp <= 0:
        return

    calc = DamageCalculator(battle_state)
    move_type = get_move_type(battle_state.current_move)

    base = calc.calculate_base_damage(
        attacker=attacker,
        defender=defender,
        move=battle_state.current_move,
        side_status=battle_state.side_statuses[target_id % 2],
        power_override=0,
        type_override=None,
        attacker_id=attacker_id,
        defender_id=target_id,
        critical_multiplier=battle_state.critical_multiplier,
        weather=battle_state.weather,
    )

    eff1 = TypeEffectiveness.get_effectiveness(move_type, defender.types[0])
    dmg = (base * eff1) // 10
    if defender.types[1] is not None and defender.types[1] != defender.types[0]:
        eff2 = TypeEffectiveness.get_effectiveness(move_type, defender.types[1])
        dmg = (dmg * eff2) // 10

    if move_type in attacker.types:
        dmg = (dmg * 15) // 10

    # Random roll 85-100%
    rand16 = rng.rand16(battle_state)
    roll = 85 + (rand16 % 16)
    dmg = (dmg * roll) // 100

    if dmg < 1:
        dmg = 1

    # Solar Beam weather penalty: halve in rain/sand/hail
    if battle_state.current_move == Move.SOLAR_BEAM:
        if battle_state.weather in (Weather.RAIN, Weather.SANDSTORM, Weather.HAIL):
            dmg //= 2

    # EQ/Magnitude vs Dig: double damage
    if battle_state.status3_underground[battle_state.battler_target]:
        # If attacker uses Earthquake or Magnitude
        if battle_state.current_move in (Move.EARTHQUAKE, Move.MAGNITUDE):
            dmg *= 2

    # Surf/Whirlpool vs Dive: double damage
    if battle_state.status3_underwater[battle_state.battler_target]:
        if battle_state.current_move in (Move.SURF, Move.WHIRLPOOL):
            dmg *= 2

    # Apply any accuracy-exception multiplier set during accuracy check
    if battle_state.damage_multiplier > 1:
        dmg *= battle_state.damage_multiplier
        battle_state.damage_multiplier = 1

    battle_state.battle_move_damage = dmg
    battle_state.script_damage = dmg

    defender.hp = max(0, defender.hp - dmg)


def is_target_invulnerable(battle_state: BattleState) -> bool:
    tid = battle_state.battler_target
    return battle_state.status3_on_air[tid] or battle_state.status3_underground[tid] or battle_state.status3_underwater[tid]


def can_hit_through_invulnerability(battle_state: BattleState) -> tuple[bool, int]:
    """
    Determine if the current move can hit a semi-invulnerable target and return (can_hit, damage_multiplier).
    Mirrors Gen 3 behavior for common exceptions.
    """
    move = battle_state.current_move
    tid = battle_state.battler_target

    # Underground (Dig)
    if battle_state.status3_underground[tid]:
        if move in (Move.EARTHQUAKE, Move.MAGNITUDE):
            return True, 2
        return False, 1

    # Underwater (Dive)
    if battle_state.status3_underwater[tid]:
        if move in (Move.SURF, Move.WHIRLPOOL):
            return True, 2
        return False, 1

    # In the air (Fly)
    if battle_state.status3_on_air[tid]:
        if move in (Move.GUST, Move.TWISTER):
            return True, 2
        if move == Move.SKY_UPPERCUT:
            # Sky Uppercut hits targets in the air (no bonus damage)
            return True, 1
        # Thunder hits while raining
        if move == Move.THUNDER and battle_state.weather == Weather.RAIN:
            return True, 1
        return False, 1

    return True, 1
