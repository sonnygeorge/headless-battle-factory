### Battle Engine High-Level Flow

```mermaid
flowchart LR
    START["Start turn<br>BE.process_turn"] --> VALIDATE_ORDER["Validate + set battler order<br>BE._validate_actions<br>BE._determine_turn_order"]
    VALIDATE_ORDER --> TURNEXEC["Execute battler turns"]

    subgraph TURNEXEC["Turn execution"]
        SORTPRIO["Sort moves by priority<br>BE._sort_moves_by_speed_and_priority"] --> ACTION_LOOP["For each battler in order<br>BE._execute_action"]
        
        subgraph ACTION_HANDLING["Action handling"]
            ACTION_LOOP -->|Move| USEMOVE["Use move<br>BE.execute_move"]
            ACTION_LOOP -->|Switch| SWITCH["Switch<br>BE._execute_switch"]

            subgraph MOVE_PIPELINE["Move pipeline"]
                USEMOVE --> SETCTX["Set ctx<br>attacker/target/move"]
                USEMOVE --> PICKSCRIPT["Pick script<br>BSL.get_script"]
                PICKSCRIPT --> RUNSCRIPT["Run script<br>BSI.execute_script"]
                
                subgraph SCRIPT_STEPS["Script steps"]
                    RUNSCRIPT --> PRECALC_CMDS["Cancel/accuracy/PP/crit<br>BSI._cmd_attackcanceler<br>BSI._cmd_accuracycheck<br>BSI._cmd_ppreduce<br>BSI._cmd_critcalc"]
                    PRECALC_CMDS --> DAMAGE_CMDS["Base dmg + final mods<br>DC.calculate_base_damage<br>DC.apply_final_damage_modifiers"]
                    DAMAGE_CMDS --> TYPE_STAB_RANDOM["Type + STAB + random<br>BSI._cmd_typecalc<br>BSI._cmd_adjustnormaldamage"]
                    TYPE_STAB_RANDOM --> HP_APPLY["Apply HP / sub / endure<br>BSI._cmd_datahpupdate"]
                    HP_APPLY --> FAINT_REPLACE["Faint + replace<br>BSI._cmd_tryfaintmon"]
                    FAINT_REPLACE --> APPLY_EFFECTS["Primary/secondary/with-chance<br>EA.apply_primary<br>EA.apply_secondary<br>EA.apply_with_chance"]
                end
            end
        end
    end

    TURNEXEC --> END_TURN_GROUP

    subgraph END_TURN_GROUP["End-of-turn effects"]
        FIELD_END_TURN["Field effects order<br>ETE._process_field_end_turn_effects"] --> BATTLER_END_TURN["Battler effects loop<br>ETE._process_battler_end_turn_effects"]
        BATTLER_END_TURN --> FUTURE_WISH["Future Sight/Wish ticks<br>ETE._process_future_sight"]
    end

    END_TURN_GROUP --> TURN_END["Increment turn & return<br>BE.process_turn"]
```

Key:
- BE: BattleEngine
- BSI: BattleScriptInterpreter
- BSL: BattleScriptLibrary
- DC: DamageCalculator
- EOT: EndTurnEffectsProcessor
- BS: BattleState
- EA: effect_applier
- ME: move_effects
- TE: TypeEffectiveness
- ETE: end_turn_effects