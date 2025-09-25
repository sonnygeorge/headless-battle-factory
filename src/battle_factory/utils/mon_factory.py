from typing import Iterable, Optional

from src.battle_factory.data.species import SPECIES_INFOS
from src.battle_factory.enums import Species, Type, Ability, Item, Move
from src.battle_factory.schema.battle_pokemon import BattlePokemon


def _compute_stat(base: int, iv: int, ev: int, level: int, is_hp: bool, nature_multiplier: float = 1.0) -> int:
    # Gen 3 stat formulas
    if is_hp:
        return ((2 * base + iv + ev // 4) * level) // 100 + level + 10
    raw = ((2 * base + iv + ev // 4) * level) // 100 + 5
    return int(raw * nature_multiplier)


def create_battle_pokemon(
    species: Species,
    level: int = 50,
    moves: Iterable[Move] | None = None,
    ability_slot: int = 0,
    iv: int = 31,
    item: Item = Item.NONE,
    nickname: Optional[str] = None,
) -> BattlePokemon:
    info = SPECIES_INFOS[species]
    # Neutral nature (1.0 multipliers) and 0 EVs for simplicity
    ev = 0
    nature = 1.0

    max_hp = _compute_stat(info.baseHP, iv, ev, level, is_hp=True)
    attack = _compute_stat(info.baseAttack, iv, ev, level, is_hp=False, nature_multiplier=nature)
    defense = _compute_stat(info.baseDefense, iv, ev, level, is_hp=False, nature_multiplier=nature)
    speed = _compute_stat(info.baseSpeed, iv, ev, level, is_hp=False, nature_multiplier=nature)
    sp_attack = _compute_stat(info.baseSpAttack, iv, ev, level, is_hp=False, nature_multiplier=nature)
    sp_defense = _compute_stat(info.baseSpDefense, iv, ev, level, is_hp=False, nature_multiplier=nature)

    ability: Ability = info.abilities[min(max(ability_slot, 0), 1)]
    mon_moves = list(moves or [])[:4]
    while len(mon_moves) < 4:
        mon_moves.append(Move.NONE)

    return BattlePokemon(
        species=species,
        attack=attack,
        defense=defense,
        speed=speed,
        spAttack=sp_attack,
        spDefense=sp_defense,
        moves=mon_moves,
        pp=[10, 10, 10, 10],
        hpIV=iv,
        attackIV=iv,
        defenseIV=iv,
        speedIV=iv,
        spAttackIV=iv,
        spDefenseIV=iv,
        isEgg=False,
        abilityNum=min(max(ability_slot, 0), 1),
        statStages=[6, 6, 6, 6, 6, 6, 6, 6],
        ability=ability,
        types=[info.types[0], info.types[1]],
        hp=max_hp,
        level=level,
        friendship=info.friendship,
        maxHP=max_hp,
        item=item,
        nickname=(nickname or species.name[:10]),
        ppBonuses=0,
        otName="OT",
        experience=0,
        personality=0,
        status1=0,
        status2=0,
        otId=0,
    )
