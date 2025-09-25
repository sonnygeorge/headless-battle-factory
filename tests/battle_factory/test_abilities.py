import math

from src.battle_factory.damage_calculator import DamageCalculator
from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.schema.battle_pokemon import BattlePokemon
from src.battle_factory.utils.mon_factory import create_battle_pokemon
from src.battle_factory.enums import Species, Ability, Item, Status1, Status2, Type, Move


def make_mon(species: Species, *, level: int = 50, ability: Ability | None = None, moves: tuple[Move, Move, Move, Move] = (Move.TACKLE, Move.NONE, Move.NONE, Move.NONE), item: Item = Item.NONE, hp_override: int | None = None) -> BattlePokemon:
    mon = create_battle_pokemon(species, level=level, moves=moves, ability_slot=0, item=item)
    if ability is not None:
        mon.ability = ability
    if hp_override is not None:
        mon.maxHP = hp_override
        mon.hp = hp_override
    return mon


def test_flash_fire_sets_boost_flag_on_fire_hit():
    bs = BattleState()
    attacker = make_mon(Species.RATTATA, moves=(Move.EMBER, Move.NONE, Move.NONE, Move.NONE))
    defender = make_mon(Species.VULPIX, ability=Ability.FLASH_FIRE, moves=(Move.NONE, Move.NONE, Move.NONE, Move.NONE))
    bs.battlers[0] = attacker
    bs.battlers[1] = defender
    calc = DamageCalculator(bs)

    # Calculate damage; Flash Fire should set boost on defender and negate damage internally
    _ = calc.calculate_base_damage(attacker, defender, Move.EMBER, 0, 0, None, attacker_id=0, defender_id=1, critical_multiplier=1, weather=0)

    assert bs.flash_fire_boosted[1] is True


def test_volt_absorb_heals_quarter_on_electric_hit():
    bs = BattleState()
    attacker = make_mon(Species.RATTATA, moves=(Move.THUNDERBOLT, Move.NONE, Move.NONE, Move.NONE))
    defender = make_mon(Species.CHINCHOU, ability=Ability.VOLT_ABSORB, hp_override=100)
    defender.hp = 60
    bs.battlers[0] = attacker
    bs.battlers[1] = defender
    calc = DamageCalculator(bs)

    _ = calc.calculate_base_damage(attacker, defender, Move.THUNDERBOLT, 0, 0, None, attacker_id=0, defender_id=1, critical_multiplier=1, weather=0)

    assert defender.hp == 60 + defender.maxHP // 4


def test_water_absorb_heals_quarter_on_water_hit():
    bs = BattleState()
    attacker = make_mon(Species.RATTATA, moves=(Move.SURF, Move.NONE, Move.NONE, Move.NONE))
    defender = make_mon(Species.LAPRAS, ability=Ability.WATER_ABSORB, hp_override=160)
    defender.hp = 100
    bs.battlers[0] = attacker
    bs.battlers[1] = defender
    calc = DamageCalculator(bs)

    _ = calc.calculate_base_damage(attacker, defender, Move.SURF, 0, 0, None, attacker_id=0, defender_id=1, critical_multiplier=1, weather=0)

    assert defender.hp == 100 + defender.maxHP // 4


def test_flash_fire_boost_increases_fire_damage():
    # Prepare a Flash Fire mon and a neutral target
    attacker_boosted = make_mon(Species.VULPIX, ability=Ability.FLASH_FIRE)
    target = make_mon(Species.RATTATA, hp_override=100)

    # Baseline (no boost)
    bs_base = BattleState()
    bs_base.battlers[0] = attacker_boosted
    bs_base.battlers[1] = target
    calc_base = DamageCalculator(bs_base)
    base = calc_base.calculate_base_damage(attacker_boosted, target, Move.EMBER, 0, 0, None, attacker_id=0, defender_id=1, critical_multiplier=1, weather=0)

    # With Flash Fire boost
    bs_ff = BattleState()
    bs_ff.battlers[0] = attacker_boosted
    bs_ff.battlers[1] = target
    # Manually set the Flash Fire boost flag for attacker
    bs_ff.flash_fire_boosted[0] = True
    calc_ff = DamageCalculator(bs_ff)
    boosted = calc_ff.calculate_base_damage(attacker_boosted, target, Move.EMBER, 0, 0, None, attacker_id=0, defender_id=1, critical_multiplier=1, weather=0)

    # Expect ~1.5x increase; allow 1-point tolerance due to integer rounding placement
    assert boosted >= max(base + 1, (base * 15) // 10 - 1)
    assert boosted > base
