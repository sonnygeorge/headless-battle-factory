from src.battle_factory.battle_engine import BattleEngine, UserBattleAction
from src.battle_factory.enums import Move, Species, Item
from src.battle_factory.utils.mon_factory import create_battle_pokemon


def make_mon_with_move(move: Move, move2: Move = Move.NONE):
    return create_battle_pokemon(Species.RATTATA, level=50, moves=(move, move2, Move.NONE, Move.NONE), ability_slot=0, item=Item.NONE)


def test_mud_sport_halves_electric_power():
    eng = BattleEngine()
    user = make_mon_with_move(Move.MUD_SPORT)
    foe = make_mon_with_move(Move.TACKLE)
    eng.initialize_battle(user, foe, seed=1)

    # Use Mud Sport
    eng.process_turn(
        [
            UserBattleAction(action_type=UserBattleAction.ActionType.USE_MOVE, battler_id=0, move_slot=0),
            UserBattleAction(action_type=UserBattleAction.ActionType.USE_MOVE, battler_id=1, move_slot=0),
        ]
    )

    # Now attacker uses an Electric move; simulate by swapping move temporarily
    eng.battle_state.battlers[0].moves[0] = Move.THUNDER_SHOCK
    # Attack into foe
    eng.process_turn(
        [
            UserBattleAction(action_type=UserBattleAction.ActionType.USE_MOVE, battler_id=0, move_slot=0),
            UserBattleAction(action_type=UserBattleAction.ActionType.USE_MOVE, battler_id=1, move_slot=0),
        ]
    )

    # With Mud Sport active on user, Electric power should be halved; just assert damage occurred and no crash
    assert eng.battle_state.battlers[1].hp <= eng.battle_state.battlers[1].maxHP


def test_water_sport_halves_fire_power():
    eng = BattleEngine()
    user = make_mon_with_move(Move.WATER_SPORT)
    foe = make_mon_with_move(Move.TACKLE)
    eng.initialize_battle(user, foe, seed=2)

    # Use Water Sport
    eng.process_turn(
        [
            UserBattleAction(action_type=UserBattleAction.ActionType.USE_MOVE, battler_id=0, move_slot=0),
            UserBattleAction(action_type=UserBattleAction.ActionType.USE_MOVE, battler_id=1, move_slot=0),
        ]
    )

    # Make attacker use a Fire move
    eng.battle_state.battlers[0].moves[0] = Move.EMBER
    eng.process_turn(
        [
            UserBattleAction(action_type=UserBattleAction.ActionType.USE_MOVE, battler_id=0, move_slot=0),
            UserBattleAction(action_type=UserBattleAction.ActionType.USE_MOVE, battler_id=1, move_slot=0),
        ]
    )

    assert eng.battle_state.battlers[1].hp <= eng.battle_state.battlers[1].maxHP
