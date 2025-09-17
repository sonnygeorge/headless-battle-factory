from src.battle_factory.schema.battle_state import BattleState


def primary_counter(battle_state: BattleState) -> None:
    """Apply Counter: reflect last physical damage taken to the recorded attacker for 2x.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectCounter)
    - pokeemerald/src/battle_script_commands.c (Cmd_counterdamagecalculator)
    """
    attacker_id = battle_state.battler_attacker
    ps = battle_state.protect_structs[attacker_id]
    if ps.physicalDmg > 0:
        target_id = ps.physicalBattlerId
        target = battle_state.battlers[target_id]
        if target is not None:
            dmg = ps.physicalDmg * 2
            target.hp = max(0, target.hp - dmg)
            battle_state.script_damage = dmg
            battle_state.battle_move_damage = dmg


def primary_mirror_coat(battle_state: BattleState) -> None:
    """Apply Mirror Coat: reflect last special damage taken to the recorded attacker for 2x.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectMirrorCoat)
    - pokeemerald/src/battle_script_commands.c (Cmd_mirrorcoatdamagecalculator)
    """
    attacker_id = battle_state.battler_attacker
    ps = battle_state.protect_structs[attacker_id]
    if ps.specialDmg > 0:
        target_id = ps.specialBattlerId
        target = battle_state.battlers[target_id]
        if target is not None:
            dmg = ps.specialDmg * 2
            target.hp = max(0, target.hp - dmg)
            battle_state.script_damage = dmg
            battle_state.battle_move_damage = dmg


def primary_magic_coat(battle_state: BattleState) -> None:
    """Apply Magic Coat: set the bounce flag for this turn on the user.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectMagicCoat)
    - pokeemerald/src/battle_script_commands.c (trysetmagiccoat)
    """
    user = battle_state.battler_attacker
    battle_state.protect_structs[user].bounceMove = True


def primary_snatch(battle_state: BattleState) -> None:
    """Apply Snatch: set the steal flag for this turn on the user.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectSnatch)
    - pokeemerald/src/battle_script_commands.c (trysetsnatch)
    """
    user = battle_state.battler_attacker
    battle_state.protect_structs[user].stealMove = True


def primary_bide(battle_state: BattleState) -> None:
    """Apply Bide setup/release behavior.

    First use: start 2-turn counter and accumulate damage while active (handled elsewhere).
    On release: deal 2x accumulated damage to the recorded target, then reset.

    Source:
    - pokeemerald/data/battle_scripts_1.s (BattleScript_EffectBide)
    - pokeemerald/src/battle_script_commands.c (Cmd_bidecalc and related)
    """
    user = battle_state.battler_attacker
    ds = battle_state.disable_structs[user]
    if ds.bideTimer == 0:
        battle_state.bide_damage[user] = 0
        battle_state.bide_target[user] = 0
        ds.bideTimer = 2
        ds.bideTimerStartValue = 2
        return
    else:
        if ds.bideTimer == 0:
            dmg = max(1, battle_state.bide_damage[user] * 2)
            target = battle_state.battlers[battle_state.bide_target[user]]
            if target is not None:
                target.hp = max(0, target.hp - dmg)
                battle_state.script_damage = dmg
                battle_state.battle_move_damage = dmg
            battle_state.bide_damage[user] = 0
            battle_state.bide_target[user] = 0
            return
