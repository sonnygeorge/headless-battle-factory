from src.battle_factory.schema.battle_state import BattleState


def advance(battle_state: BattleState) -> int:
    """Advance the LCG RNG and return the new 32-bit seed.

    Mirrors Emerald's RNG: seed = (seed * 1664525 + 1013904223) mod 2^32
    """
    battle_state.rng_seed = (battle_state.rng_seed * 1664525 + 1013904223) & 0xFFFFFFFF
    return battle_state.rng_seed


def rand16(battle_state: BattleState) -> int:
    """Advance RNG and return upper 16 bits (0..65535)."""
    advance(battle_state)
    return (battle_state.rng_seed >> 16) & 0xFFFF


def choice_index(battle_state: BattleState, count: int) -> int:
    """Return a random index in range [0, count) using rand16 modulo.

    Caller must ensure count > 0. Uses upper 16 bits like the game.
    """
    if count <= 0:
        return -1
    return rand16(battle_state) % count
