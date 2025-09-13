from enum import IntEnum
from src.battle_factory.enums import MoveEffect, HoldEffect, Ability, Species
from src.battle_factory.damage_calculator import DamageCalculator
from src.battle_factory.type_effectiveness import TypeEffectiveness
from src.battle_factory.data.moves import get_move_effect, get_move_type
from src.battle_factory.data.items import get_hold_effect
from src.battle_factory.schema.battle_state import BattleState
from src.battle_factory.schema.battle_pokemon import BattlePokemon


class BattleScriptCommand(IntEnum):
    """
    Battle script commands - from pokeemerald/src/battle_script_commands.c

    These are the exact opcodes used in the C battle script system.
    Each command corresponds to a specific battle function.
    """

    # Core battle flow commands (lines 331-342 in C)
    ATTACKCANCELER = 0x0  # Check if attack should be cancelled
    ACCURACYCHECK = 0x1  # Check if move hits
    ATTACKSTRING = 0x2  # Print attack message
    PPREDUCE = 0x3  # Reduce PP
    CRITCALC = 0x4  # Calculate critical hit
    DAMAGECALC = 0x5  # Calculate damage
    TYPECALC = 0x6  # Calculate type effectiveness
    ADJUSTNORMALDAMAGE = 0x7  # Apply damage modifiers
    ADJUSTNORMALDAMAGE2 = 0x8  # Apply more damage modifiers

    # Animation and display commands (lines 340-350 in C)
    # Note: These will be stubbed for headless operation
    ATTACKANIMATION = 0x9  # Play attack animation
    WAITANIMATION = 0xA  # Wait for animation
    HEALTHBARUPDATE = 0xB  # Update HP bar
    DATAHPUPDATE = 0xC  # Update HP data
    CRITMESSAGE = 0xD  # Print crit message
    EFFECTIVENESSSOUND = 0xE  # Play effectiveness sound
    RESULTMESSAGE = 0xF  # Print result message

    # Text and messaging commands (lines 347-351 in C)
    PRINTSTRING = 0x10  # Print battle text
    PRINTSELECTIONSTRING = 0x11  # Print selection text
    WAITMESSAGE = 0x12  # Wait for message
    PRINTFROMTABLE = 0x13  # Print from string table
    PRINTSELECTIONSTRINGFROMTABLE = 0x14

    # Status effect commands (lines 352-358 in C)
    SETEFFECTWITHCHANCE = 0x15  # Set effect with chance
    SETEFFECTPRIMARY = 0x16  # Set primary effect
    SETEFFECTSECONDARY = 0x17  # Set secondary effect
    CLEARSTATUSFROMEFFECT = 0x18  # Clear status

    # Fainting commands (lines 356-358 in C)
    TRYFAINTMON = 0x19  # Check if mon should faint
    DOFAINTANIMATION = 0x1A  # Play faint animation
    CLEAREFFECTSONFAINT = 0x1B  # Clear effects when fainting

    # Conditional jump commands (lines 359-362 in C)
    JUMPIFSTATUS = 0x1C  # Jump if status condition
    JUMPIFSTATUS2 = 0x1D  # Jump if status2 condition
    JUMPIFABILITY = 0x1E  # Jump if ability
    JUMPIFSIDEAFFECTING = 0x1F  # Jump if side effect

    # Control flow commands
    CALL = 0x58  # Call subroutine
    GOTO = 0x59  # Unconditional jump
    END = 0x5A  # End script
    RETURN = 0x47  # Return from subroutine

    # Special commands
    PAUSE = 0x60  # Pause execution
    NOP = 0x61  # No operation


class BattleScript:
    """
    A battle script - sequence of commands with arguments

    In the C code, this is represented as a byte array (const u8 *).
    We're making it more structured while maintaining the same behavior.

    Example C battle script:
        static const u8 BattleScript_EffectHit[] = {
            attackcanceler,
            accuracycheck,
            attackstring,
            ppreduce,
            critcalc,
            damagecalc,
            typecalc,
            adjustnormaldamage,
            attackanimation,
            waitanimation,
            datahpupdate,
            tryfaintmon,
            seteffectsecondary,
            end
        };
    """

    def __init__(self, commands: list[BattleScriptCommand | int]):
        """
        Initialize battle script with command sequence

        Args:
            commands: list of commands and arguments (ints are treated as raw bytes/args)
        """
        self.commands = commands
        self.pc = 0  # Program counter (instruction pointer)

    def reset(self) -> None:
        """Reset script to beginning - equivalent to setting gBattlescriptCurrInstr"""
        self.pc = 0

    def read_byte(self) -> int:
        """
        Read next byte and advance PC

        Equivalent to:
            value = *gBattlescriptCurrInstr;
            gBattlescriptCurrInstr++;
        """
        if self.pc >= len(self.commands):
            return 0
        value = self.commands[self.pc]
        self.pc += 1
        return int(value)

    def read_word(self) -> int:
        """
        Read next 2 bytes as 16-bit word (little-endian)

        Equivalent to:
            value = T1_READ_16(gBattlescriptCurrInstr);
            gBattlescriptCurrInstr += 2;
        """
        low = self.read_byte()
        high = self.read_byte()
        return (high << 8) | low

    def read_ptr(self) -> int:
        """
        Read next 4 bytes as 32-bit pointer/address

        Equivalent to:
            value = T1_READ_PTR(gBattlescriptCurrInstr);
            gBattlescriptCurrInstr += 4;
        """
        b0 = self.read_byte()
        b1 = self.read_byte()
        b2 = self.read_byte()
        b3 = self.read_byte()
        return (b3 << 24) | (b2 << 16) | (b1 << 8) | b0

    def jump_to(self, address: int) -> None:
        """
        Jump to specific address in script

        Equivalent to:
            gBattlescriptCurrInstr = address;
        """
        if 0 <= address < len(self.commands):
            self.pc = address

    def is_finished(self) -> bool:
        """Check if script has finished executing"""
        return self.pc >= len(self.commands)

    def get_current_position(self) -> int:
        """Get current position (for stack operations)"""
        return self.pc

    def set_position(self, position: int) -> None:
        """Set current position (for stack operations)"""
        if 0 <= position <= len(self.commands):
            self.pc = position


class BattleScriptInterpreter:
    """
    Battle script interpreter - mirrors the C implementation

    This class executes battle scripts command by command, maintaining state like the
    original gBattlescriptCurrInstr system from pokeemerald.

    Equivalent C functions:
    - RunBattleScriptCommands() - main script execution loop
    - gBattleScriptingCommandsTable[] - command dispatch table
    - BattleScriptExecute() - script initialization
    """

    def __init__(self):
        """
        Initialize the battle script interpreter

        Note: The actual battle state will be passed to execute_script()
        to maintain separation of concerns.
        """
        # Script execution stack (equivalent to gBattleResources->battleScriptsStack)
        self.script_stack: list[BattleScript] = []

        # Current script being executed (equivalent to gBattlescriptCurrInstr)
        self.current_script: BattleScript | None = None

        # Damage calculator for script commands
        self.damage_calculator = DamageCalculator()

        # Command function dispatch table - maps opcodes to methods
        # This mirrors gBattleScriptingCommandsTable[] from C (lines 329-362)
        self.command_table: dict[BattleScriptCommand, str] = {
            # Core battle flow commands
            BattleScriptCommand.ATTACKCANCELER: "_cmd_attackcanceler",
            BattleScriptCommand.ACCURACYCHECK: "_cmd_accuracycheck",
            BattleScriptCommand.ATTACKSTRING: "_cmd_attackstring",
            BattleScriptCommand.PPREDUCE: "_cmd_ppreduce",
            BattleScriptCommand.CRITCALC: "_cmd_critcalc",
            BattleScriptCommand.DAMAGECALC: "_cmd_damagecalc",
            BattleScriptCommand.TYPECALC: "_cmd_typecalc",
            BattleScriptCommand.ADJUSTNORMALDAMAGE: "_cmd_adjustnormaldamage",
            BattleScriptCommand.ADJUSTNORMALDAMAGE2: "_cmd_adjustnormaldamage2",
            # Animation and display commands (stubbed for headless)
            BattleScriptCommand.ATTACKANIMATION: "_cmd_stub",
            BattleScriptCommand.WAITANIMATION: "_cmd_stub",
            BattleScriptCommand.HEALTHBARUPDATE: "_cmd_stub",
            BattleScriptCommand.DATAHPUPDATE: "_cmd_datahpupdate",
            BattleScriptCommand.CRITMESSAGE: "_cmd_stub",
            BattleScriptCommand.EFFECTIVENESSSOUND: "_cmd_stub",
            BattleScriptCommand.RESULTMESSAGE: "_cmd_stub",
            # Text commands (stubbed for headless)
            BattleScriptCommand.PRINTSTRING: "_cmd_stub",
            BattleScriptCommand.PRINTSELECTIONSTRING: "_cmd_stub",
            BattleScriptCommand.WAITMESSAGE: "_cmd_stub",
            BattleScriptCommand.PRINTFROMTABLE: "_cmd_stub",
            BattleScriptCommand.PRINTSELECTIONSTRINGFROMTABLE: "_cmd_stub",
            # Status effect commands
            BattleScriptCommand.SETEFFECTWITHCHANCE: "_cmd_seteffectwithchance",
            BattleScriptCommand.SETEFFECTPRIMARY: "_cmd_seteffectprimary",
            BattleScriptCommand.SETEFFECTSECONDARY: "_cmd_seteffectsecondary",
            BattleScriptCommand.CLEARSTATUSFROMEFFECT: "_cmd_clearstatusfromeffect",
            # Fainting commands
            BattleScriptCommand.TRYFAINTMON: "_cmd_tryfaintmon",
            BattleScriptCommand.DOFAINTANIMATION: "_cmd_stub",
            BattleScriptCommand.CLEAREFFECTSONFAINT: "_cmd_cleareffectsonfaint",
            # Conditional jump commands
            BattleScriptCommand.JUMPIFSTATUS: "_cmd_jumpifstatus",
            BattleScriptCommand.JUMPIFSTATUS2: "_cmd_jumpifstatus2",
            BattleScriptCommand.JUMPIFABILITY: "_cmd_jumpifability",
            BattleScriptCommand.JUMPIFSIDEAFFECTING: "_cmd_jumpifsideaffecting",
            # Control flow commands
            BattleScriptCommand.CALL: "_cmd_call",
            BattleScriptCommand.GOTO: "_cmd_goto",
            BattleScriptCommand.END: "_cmd_end",
            BattleScriptCommand.RETURN: "_cmd_return",
            BattleScriptCommand.PAUSE: "_cmd_pause",
            BattleScriptCommand.NOP: "_cmd_stub",
        }

    def execute_script(self, script: BattleScript, battle_state: BattleState) -> bool:
        """
        Execute a battle script - equivalent to BattleScriptExecute() in C

        Args:
            script: The battle script to execute
            battle_state: Current battle state (will be properly typed later)

        Returns:
            True if script finished completely, False if paused/waiting

        Equivalent C code:
            void BattleScriptExecute(const u8 *BS_ptr) {
                gBattlescriptCurrInstr = BS_ptr;
                // ... callback setup ...
                gBattleMainFunc = RunBattleScriptCommands;
            }
        """
        self.current_script = script
        script.reset()

        # Main execution loop - equivalent to RunBattleScriptCommands() in C
        while not script.is_finished():
            # Read command opcode
            command_byte = script.read_byte()

            # Validate command
            if command_byte not in self.command_table:
                raise ValueError(f"Unknown battle script command: 0x{command_byte:02X}")

            command = BattleScriptCommand(command_byte)
            method_name = self.command_table[command]

            # Execute command method
            # In C: gBattleScriptingCommandsTable[command]();
            method = getattr(self, method_name)
            result = method(battle_state)

            # If command returns False, script is paused (waiting for animation, etc.)
            if result is False:
                return False

        return True

    def script_push(self, script: BattleScript) -> None:
        """Push script to stack - equivalent to BattleScriptPush() in C"""
        self.script_stack.append(self.current_script)

    def script_pop(self) -> None:
        """Pop script from stack - equivalent to BattleScriptPop() in C"""
        if self.script_stack:
            self.current_script = self.script_stack.pop()

    # ==========================================================================
    # BATTLE SCRIPT COMMAND IMPLEMENTATIONS
    # ==========================================================================
    # Note: These methods will be implemented carefully in the next step
    # Each one corresponds to a Cmd_* function in battle_script_commands.c

    def _cmd_attackcanceler(self, battle_state: BattleState) -> bool:
        """
        Check if attack should be cancelled - mirrors Cmd_attackcanceler()

        C location: src/battle_script_commands.c line ~1000
        Checks for: sleep, paralysis, flinch, attraction, etc.
        """
        # TODO: Implement attack cancellation checks
        # For now, allow all attacks to proceed
        return True

    def _cmd_accuracycheck(self, battle_state: BattleState) -> bool:
        """
        Check move accuracy - mirrors Cmd_accuracycheck()

        C location: src/battle_script_commands.c line ~1100
        """
        # TODO: Implement accuracy calculation
        # For now, assume all moves hit
        return True

    def _cmd_attackstring(self, battle_state: BattleState) -> bool:
        """
        Print attack message - mirrors Cmd_attackstring()

        C location: src/battle_script_commands.c line ~800
        In headless mode, we can log or ignore this
        """
        # Stub for headless operation
        return True

    def _cmd_ppreduce(self, battle_state: BattleState) -> bool:
        """
        Reduce PP - mirrors Cmd_ppreduce()

        C location: src/battle_script_commands.c line ~900
        """
        # TODO: Implement PP reduction
        return True

    def _cmd_critcalc(self, battle_state: BattleState) -> bool:
        """
        Calculate critical hit chance and set critical multiplier.

        C equivalent: src/battle_script_commands.c lines 1253-1288

        This command determines if the current move will be a critical hit based on
        various factors like Focus Energy, high-crit moves, held items, and abilities.

        Args:
            battle_state: Current battle state containing attacker, target, move, and RNG seed.
                         Must have battler_attacker, battler_target, current_move, and rng_seed set.

        Returns:
            bool: Always True (command never pauses). The critical hit result is stored
                  in battle_state.critical_multiplier (1 = normal hit, 2 = critical hit).

        Modifies:
            battle_state.critical_multiplier: Set to 1 (normal) or 2 (critical hit)
            battle_state.rng_seed: Updated for deterministic random number generation
        """

        # Get attacker and their item
        attacker = battle_state.battlers[battle_state.battler_attacker]
        if attacker is None:
            battle_state.critical_multiplier = 1
            return True

        # Get hold effect from item
        hold_effect = get_hold_effect(attacker.item)

        # Calculate critical hit chance - exact formula from C code
        crit_chance = 0

        # Focus Energy adds +2 (STATUS2_FOCUS_ENERGY)
        if attacker.status2.has_focus_energy():
            crit_chance += 2

        # High crit moves add +1 (EFFECT_HIGH_CRITICAL)
        move_effect = get_move_effect(battle_state.current_move)
        if move_effect == MoveEffect.HIGH_CRITICAL:
            crit_chance += 1

        # Special move effects that boost crit chance
        if move_effect == MoveEffect.SKY_ATTACK:
            crit_chance += 1
        if move_effect == MoveEffect.BLAZE_KICK:
            crit_chance += 1
        if move_effect == MoveEffect.POISON_TAIL:
            crit_chance += 1

        # Hold effects
        if hold_effect == HoldEffect.SCOPE_LENS:
            crit_chance += 1
        if hold_effect == HoldEffect.LUCKY_PUNCH and attacker.species == Species.CHANSEY:
            crit_chance += 2
        if hold_effect == HoldEffect.STICK and attacker.species == Species.FARFETCHD:
            crit_chance += 2

        # Clamp to valid range (sCriticalHitChance array has 5 elements)
        CRIT_CHANCE_TABLE = [16, 8, 4, 3, 2]  # 1/N chance from original C code
        if crit_chance >= len(CRIT_CHANCE_TABLE):
            crit_chance = len(CRIT_CHANCE_TABLE) - 1

        # Check for crit prevention abilities
        defender = battle_state.battlers[battle_state.battler_target]
        if defender is not None and defender.ability in [Ability.BATTLE_ARMOR, Ability.SHELL_ARMOR]:
            battle_state.critical_multiplier = 1
            return True

        # Check for other crit prevention (status3 flags, tutorial battles, etc.)
        # TODO: Implement STATUS3_CANT_SCORE_A_CRIT, tutorial battle flags
        # For now, skip these checks as they're not relevant to Battle Factory

        # Roll for critical hit using battle state RNG
        if self._random_crit_roll(battle_state) % CRIT_CHANCE_TABLE[crit_chance] == 0:
            battle_state.critical_multiplier = 2
        else:
            battle_state.critical_multiplier = 1

        return True

    def _cmd_damagecalc(self, battle_state: BattleState) -> bool:
        """Calculate damage - mirrors Cmd_damagecalc()"""
        # Get attacker and defender
        attacker = battle_state.battlers[battle_state.battler_attacker]
        defender = battle_state.battlers[battle_state.battler_target]

        if attacker is None or defender is None:
            battle_state.battle_move_damage = 0
            return True

        # Get defender's side status (Reflect, Light Screen, etc.)
        defender_side = battle_state.battler_target % 2  # 0 = player side, 1 = opponent side
        side_status = battle_state.side_statuses[defender_side]

        # Calculate base damage using damage calculator
        base_damage = self.damage_calculator.calculate_base_damage(
            attacker=attacker,
            defender=defender,
            move=battle_state.current_move,
            side_status=side_status,
            power_override=0,
            type_override=None,
            attacker_id=battle_state.battler_attacker,
            defender_id=battle_state.battler_target,
            critical_multiplier=battle_state.critical_multiplier,
            weather=battle_state.weather,
        )  # TODO: Handle gDynamicBasePower  # TODO: Handle gBattleStruct->dynamicMoveType

        # Apply final modifiers (critical hit, damage multiplier)
        final_damage = self.damage_calculator.apply_final_damage_modifiers(
            base_damage=base_damage,
            critical_multiplier=battle_state.critical_multiplier,
            dmg_multiplier=1,
            attacker=attacker,
            move=battle_state.current_move,
        )  # TODO: Handle gBattleScripting.dmgMultiplier

        # Store result in battle state
        battle_state.battle_move_damage = final_damage
        battle_state.script_damage = final_damage

        return True

    def _cmd_typecalc(self, battle_state: BattleState) -> bool:
        """
        Calculate type effectiveness - mirrors ModulateDmgByType()

        C location: src/battle_script_commands.c line ~1321

        This command applies type effectiveness to the current damage value.
        """
        # Get attacker and defender
        attacker = battle_state.battlers[battle_state.battler_attacker]
        defender = battle_state.battlers[battle_state.battler_target]

        if attacker is None or defender is None:
            return True

        # Get move type (TODO: handle type-changing abilities/items)
        move_type = get_move_type(battle_state.current_move)

        # Calculate against both types (handles single or dual-type Pokemon)
        effectiveness = TypeEffectiveness.calculate_effectiveness(
            attacking_type=move_type,
            defending_type1=defender.types[0],
            defending_type2=defender.types[1] if defender.types[1] != defender.types[0] else None,
        )

        # Apply type effectiveness to damage
        battle_state.battle_move_damage = (battle_state.battle_move_damage * effectiveness) // 10
        battle_state.type_effectiveness = effectiveness
        battle_state.script_type_effectiveness = effectiveness

        return True

    def _cmd_adjustnormaldamage(self, battle_state: BattleState) -> bool:
        """
        Apply damage modifiers - mirrors Cmd_adjustnormaldamage()

        C location: src/battle_script_commands.c line ~1600

        This applies STAB, random damage factor, and other final modifiers.
        """
        # Get attacker for STAB check
        attacker = battle_state.battlers[battle_state.battler_attacker]
        if attacker is None:
            return True

        # Get move type
        move_type = get_move_type(battle_state.current_move)

        # Apply STAB (Same Type Attack Bonus) - 1.5x damage
        if move_type in attacker.types:
            battle_state.battle_move_damage = (battle_state.battle_move_damage * 15) // 10

        # Apply random damage factor (85-100% of calculated damage)
        # In the original game: damage = damage * random(85, 100) / 100
        # For now, use a fixed 92% to maintain determinism
        battle_state.battle_move_damage = (battle_state.battle_move_damage * 92) // 100

        # Ensure minimum damage of 1
        if battle_state.battle_move_damage < 1:
            battle_state.battle_move_damage = 1

        return True

    def _cmd_adjustnormaldamage2(self, battle_state: BattleState) -> bool:
        """
        Apply additional damage modifiers - mirrors Cmd_adjustnormaldamage2()

        C location: src/battle_script_commands.c line ~1700
        """
        # TODO: Implement additional damage modifiers (STAB, items, abilities)
        return True

    def _cmd_datahpupdate(self, battle_state: BattleState) -> bool:
        """
        Update HP data - mirrors Cmd_datahpupdate()

        C location: src/battle_script_commands.c line ~1800

        This command applies the calculated damage to the target's HP.
        """
        # Get target Pokemon
        target = battle_state.battlers[battle_state.battler_target]
        if target is None:
            return True

        # Apply damage to target's HP
        damage = battle_state.battle_move_damage
        target.hp = max(0, target.hp - damage)

        return True

    def _cmd_tryfaintmon(self, battle_state: BattleState) -> bool:
        """
        Check if Pokemon should faint - mirrors Cmd_tryfaintmon()

        C location: src/battle_script_commands.c line ~2000

        This command checks if the target Pokemon has fainted (HP <= 0).
        """
        # Get target Pokemon
        target = battle_state.battlers[battle_state.battler_target]
        if target is None:
            return True

        # Check if Pokemon has fainted
        if target.hp <= 0:
            target.hp = 0
            # TODO: Set faint status, clear temporary effects, etc.
            # For now, just ensure HP is exactly 0

        return True

    def _cmd_seteffectwithchance(self, battle_state: BattleState) -> bool:
        """Set move effect with chance - mirrors Cmd_seteffectwithchance()"""
        # TODO: Implement secondary effect chances
        return True

    def _cmd_seteffectprimary(self, battle_state: BattleState) -> bool:
        """Set primary effect - mirrors Cmd_seteffectprimary()"""
        # TODO: Implement primary move effects
        return True

    def _cmd_seteffectsecondary(self, battle_state: BattleState) -> bool:
        """Set secondary effect - mirrors Cmd_seteffectsecondary()"""
        # TODO: Implement secondary move effects
        return True

    def _cmd_clearstatusfromeffect(self, battle_state: BattleState) -> bool:
        """Clear status from effect - mirrors Cmd_clearstatusfromeffect()"""
        # TODO: Implement status clearing
        return True

    def _cmd_cleareffectsonfaint(self, battle_state: BattleState) -> bool:
        """Clear effects when fainting - mirrors Cmd_cleareffectsonfaint()"""
        # TODO: Clear all temporary effects on the fainted Pokemon
        return True

    # ==========================================================================
    # CONDITIONAL COMMANDS (read arguments from script)
    # ==========================================================================

    def _cmd_jumpifstatus(self, battle_state: BattleState) -> bool:
        """
        Jump if status condition - mirrors Cmd_jumpifstatus()

        Script format: JUMPIFSTATUS battler status jump_address
        """
        battler_byte = self.current_script.read_byte()
        status_byte = self.current_script.read_byte()
        jump_addr = self.current_script.read_ptr()

        # TODO: Implement status checking
        # if condition_met:
        #     self.current_script.jump_to(jump_addr)

        return True

    def _cmd_jumpifstatus2(self, battle_state: BattleState) -> bool:
        """Jump if status2 condition - mirrors Cmd_jumpifstatus2()"""
        battler_byte = self.current_script.read_byte()
        status_byte = self.current_script.read_byte()
        jump_addr = self.current_script.read_ptr()

        # TODO: Implement status2 checking
        return True

    def _cmd_jumpifability(self, battle_state: BattleState) -> bool:
        """Jump if ability - mirrors Cmd_jumpifability()"""
        battler_byte = self.current_script.read_byte()
        ability_byte = self.current_script.read_byte()
        jump_addr = self.current_script.read_ptr()

        # TODO: Implement ability checking
        return True

    def _cmd_jumpifsideaffecting(self, battle_state: BattleState) -> bool:
        """Jump if side effect - mirrors Cmd_jumpifsideaffecting()"""
        side_byte = self.current_script.read_byte()
        effect_word = self.current_script.read_word()
        jump_addr = self.current_script.read_ptr()

        # TODO: Implement side effect checking
        return True

    # ==========================================================================
    # CONTROL FLOW COMMANDS
    # ==========================================================================

    def _cmd_call(self, battle_state: BattleState) -> bool:
        """
        Call subroutine - mirrors Cmd_call()

        C location: src/battle_script_commands.c line ~3975

        C code:
            static void Cmd_call(void) {
                BattleScriptPush(gBattlescriptCurrInstr + 5);
                gBattlescriptCurrInstr = T1_READ_PTR(gBattlescriptCurrInstr + 1);
            }
        """
        subroutine_addr = self.current_script.read_ptr()

        # Push current position to stack (equivalent to gBattlescriptCurrInstr + 5)
        self.script_push(self.current_script)

        # TODO: Jump to subroutine address
        # For now, this is a placeholder until we implement script address resolution

        return True

    def _cmd_goto(self, battle_state: BattleState) -> bool:
        """
        Unconditional jump - mirrors Cmd_goto()

        Script format: GOTO jump_address
        """
        jump_addr = self.current_script.read_ptr()
        self.current_script.jump_to(jump_addr)
        return True

    def _cmd_return(self, battle_state: BattleState) -> bool:
        """
        Return from subroutine - mirrors Cmd_return()

        C location: src/battle_script_commands.c line ~3945

        C code:
            static void Cmd_return(void) {
                gBattlescriptCurrInstr = BattleScriptPop();
            }
        """
        self.script_pop()
        return True

    def _cmd_end(self, battle_state: BattleState) -> bool:
        """
        End script - mirrors Cmd_end()

        C location: src/battle_script_commands.c line ~3950
        """
        # Mark script as finished by setting PC to end
        self.current_script.pc = len(self.current_script.commands)
        return True

    def _cmd_pause(self, battle_state: BattleState) -> bool:
        """Pause execution - returns False to pause interpreter"""
        return False

    def _cmd_stub(self, battle_state: BattleState) -> bool:
        """Stub for unimplemented/skipped commands (animations, etc.)"""
        return True

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _random_crit_roll(self, battle_state: BattleState) -> int:
        """
        Generate random number for critical hit calculation using battle RNG

        This uses the same RNG system as the original game for deterministic results.

        Args:
            battle_state: Current battle state containing RNG seed

        Returns:
            Random integer for crit calculation
        """
        # Use Linear Congruential Generator (LCG) for deterministic random numbers
        # This matches the Random() function behavior in the original game
        battle_state.rng_seed = (battle_state.rng_seed * 1664525 + 1013904223) & 0xFFFFFFFF
        return battle_state.rng_seed


class BattleScriptLibrary:
    """
    Collection of pre-defined battle scripts for all move effects

    Mirrors the gBattleScriptsForMoveEffects[] table from pokeemerald/data/battle_scripts_1.s

    Each script defines the exact sequence of battle commands that execute when a move
    with that effect is used. GUI/animation commands are omitted for headless operation.

    Key differences from C implementation:
    - No animation commands (attackanimation, waitanimation, etc.)
    - No text display commands (attackstring, critmessage, etc.)
    - No arbitrary waits (waitmessage, pause)
    - Focus purely on battle mechanics and state changes
    """

    def __init__(self):
        """Initialize the battle script library with all move effect scripts"""
        self.scripts: dict[MoveEffect, BattleScript] = {
            # =================================================================
            # BASIC DAMAGE MOVES
            # =================================================================
            MoveEffect.HIT: BattleScript(
                [
                    # Core battle flow - mirrors BattleScript_EffectHit
                    BattleScriptCommand.ATTACKCANCELER,  # Check if attack cancelled
                    BattleScriptCommand.ACCURACYCHECK,  # Check if move hits
                    BattleScriptCommand.PPREDUCE,  # Reduce PP
                    BattleScriptCommand.CRITCALC,  # Calculate critical hit
                    BattleScriptCommand.DAMAGECALC,  # Calculate base damage
                    BattleScriptCommand.TYPECALC,  # Apply type effectiveness
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,  # Apply all damage modifiers
                    BattleScriptCommand.DATAHPUPDATE,  # Update target HP
                    BattleScriptCommand.TRYFAINTMON,  # Check if target faints
                    BattleScriptCommand.SETEFFECTSECONDARY,  # Apply secondary effects
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.ALWAYS_HIT: BattleScript(
                [
                    # Always hits - skip accuracy check
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,
                    BattleScriptCommand.TRYFAINTMON,
                    BattleScriptCommand.SETEFFECTSECONDARY,
                    BattleScriptCommand.END,
                ]
            ),
            # =================================================================
            # STATUS EFFECT DAMAGE MOVES
            # =================================================================
            MoveEffect.POISON_HIT: BattleScript(
                [
                    # Damage + chance to poison - mirrors BattleScript_EffectPoisonHit
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,
                    BattleScriptCommand.TRYFAINTMON,
                    BattleScriptCommand.SETEFFECTWITHCHANCE,  # Try to apply poison
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.BURN_HIT: BattleScript(
                [
                    # Damage + chance to burn
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,
                    BattleScriptCommand.TRYFAINTMON,
                    BattleScriptCommand.SETEFFECTWITHCHANCE,  # Try to apply burn
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.FREEZE_HIT: BattleScript(
                [
                    # Damage + chance to freeze
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,
                    BattleScriptCommand.TRYFAINTMON,
                    BattleScriptCommand.SETEFFECTWITHCHANCE,  # Try to apply freeze
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.PARALYZE_HIT: BattleScript(
                [
                    # Damage + chance to paralyze
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,
                    BattleScriptCommand.TRYFAINTMON,
                    BattleScriptCommand.SETEFFECTWITHCHANCE,  # Try to apply paralysis
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.FLINCH_HIT: BattleScript(
                [
                    # Damage + chance to flinch
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,
                    BattleScriptCommand.TRYFAINTMON,
                    BattleScriptCommand.SETEFFECTWITHCHANCE,  # Try to apply flinch
                    BattleScriptCommand.END,
                ]
            ),
            # =================================================================
            # PURE STATUS MOVES
            # =================================================================
            MoveEffect.SLEEP: BattleScript(
                [
                    # Pure sleep move - mirrors BattleScript_EffectSleep
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,  # Apply sleep as primary effect
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.TOXIC: BattleScript(
                [
                    # Badly poison move
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,  # Apply toxic poison
                    BattleScriptCommand.END,
                ]
            ),
            # =================================================================
            # STAT MODIFICATION MOVES
            # =================================================================
            MoveEffect.ATTACK_UP: BattleScript(
                [
                    # Raise user's Attack by 1 stage - mirrors BattleScript_EffectAttackUp
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,  # Apply stat boost
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.DEFENSE_UP: BattleScript(
                [
                    # Raise user's Defense by 1 stage
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.SPEED_UP: BattleScript(
                [
                    # Raise user's Speed by 1 stage
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.SPECIAL_ATTACK_UP: BattleScript(
                [
                    # Raise user's Special Attack by 1 stage
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.SPECIAL_DEFENSE_UP: BattleScript(
                [
                    # Raise user's Special Defense by 1 stage
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.ATTACK_DOWN: BattleScript(
                [
                    # Lower target's Attack by 1 stage
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.DEFENSE_DOWN: BattleScript(
                [
                    # Lower target's Defense by 1 stage
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.SPEED_DOWN: BattleScript(
                [
                    # Lower target's Speed by 1 stage
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.SETEFFECTPRIMARY,
                    BattleScriptCommand.END,
                ]
            ),
            # =================================================================
            # SPECIAL DAMAGE CALCULATIONS
            # =================================================================
            MoveEffect.ABSORB: BattleScript(
                [
                    # Damage that heals user for half damage dealt
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,  # Damage target
                    BattleScriptCommand.TRYFAINTMON,
                    # TODO: Add absorb healing logic in command implementation
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.RECOIL: BattleScript(
                [
                    # High power move with recoil damage
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,  # Damage target
                    BattleScriptCommand.TRYFAINTMON,
                    # TODO: Add recoil damage logic
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.MULTI_HIT: BattleScript(
                [
                    # Hits 2-5 times - mirrors BattleScript_EffectMultiHit
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    # TODO: Add multi-hit loop logic
                    BattleScriptCommand.CRITCALC,
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,
                    BattleScriptCommand.TRYFAINTMON,
                    BattleScriptCommand.END,
                ]
            ),
            # =================================================================
            # UTILITY MOVES
            # =================================================================
            MoveEffect.RESTORE_HP: BattleScript(
                [
                    # Healing moves like Recover
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.PPREDUCE,
                    # TODO: Add HP restoration logic
                    BattleScriptCommand.END,
                ]
            ),
            MoveEffect.REST: BattleScript(
                [
                    # Rest - sleep for 2 turns and restore all HP
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.PPREDUCE,
                    # TODO: Add Rest logic (full heal + sleep)
                    BattleScriptCommand.END,
                ]
            ),
            # =================================================================
            # HIGH CRITICAL RATIO
            # =================================================================
            MoveEffect.HIGH_CRITICAL: BattleScript(
                [
                    # High critical hit ratio moves (Karate Chop, Razor Leaf, etc.)
                    BattleScriptCommand.ATTACKCANCELER,
                    BattleScriptCommand.ACCURACYCHECK,
                    BattleScriptCommand.PPREDUCE,
                    BattleScriptCommand.CRITCALC,  # Uses higher crit rate
                    BattleScriptCommand.DAMAGECALC,
                    BattleScriptCommand.TYPECALC,
                    BattleScriptCommand.ADJUSTNORMALDAMAGE,
                    BattleScriptCommand.DATAHPUPDATE,
                    BattleScriptCommand.TRYFAINTMON,
                    BattleScriptCommand.END,
                ]
            ),
        }

        # Add default script for any missing effects
        self._add_default_scripts()

    def _add_default_scripts(self) -> None:
        """Add default scripts for any move effects not explicitly implemented"""
        default_script = self.scripts[MoveEffect.HIT]  # Use basic hit as default

        for effect in MoveEffect:
            if effect not in self.scripts:
                self.scripts[effect] = default_script

    def get_script(self, effect: MoveEffect) -> BattleScript:
        """
        Get the battle script for a move effect

        Args:
            effect: The move effect to get the script for

        Returns:
            BattleScript object containing the command sequence
        """
        return self.scripts[effect]

    def get_implemented_effects(self) -> list[MoveEffect]:
        """Get list of move effects that have been properly implemented (not defaults)"""
        implemented = []
        default_script = self.scripts[MoveEffect.HIT]

        for effect, script in self.scripts.items():
            if script is not default_script:  # Not using default
                implemented.append(effect)

        return implemented
