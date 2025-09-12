from enum import IntFlag


class Status1(IntFlag):
    """Non-volatile status conditions - from include/constants/battle.h"""

    NONE = 0
    SLEEP = (1 << 0) | (1 << 1) | (1 << 2)  # First 3 bits (Number of turns to sleep)
    POISON = 1 << 3
    BURN = 1 << 4
    FREEZE = 1 << 5
    PARALYSIS = 1 << 6
    TOXIC_POISON = 1 << 7
    TOXIC_COUNTER = (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11)
    PSN_ANY = POISON | TOXIC_POISON
    ANY = SLEEP | POISON | BURN | FREEZE | PARALYSIS | TOXIC_POISON

    # =========================================================================
    # C MACRO EQUIVALENTS - Make masks and shifts public for external use
    # =========================================================================

    # Public masks (equivalent to C macros)
    SLEEP_MASK = 0b111  # 3 bits for sleep counter (0-7)
    TOXIC_MASK = 0b1111 << 8  # 4 bits for toxic counter (0-15)

    # Shift values for readability
    SLEEP_SHIFT = 0
    TOXIC_SHIFT = 8

    # =========================================================================
    # C MACRO FACTORY METHODS - Equivalent to STATUS1_SLEEP_TURN(num), etc.
    # =========================================================================

    @classmethod
    def sleep_turn(cls, num: int) -> "Status1":
        """Create sleep status with specified turns - equivalent to STATUS1_SLEEP_TURN(num)"""
        if not 0 <= num <= 7:
            raise ValueError("Sleep turns must be 0-7")
        return cls(num << cls.SLEEP_SHIFT)

    @classmethod
    def toxic_turn(cls, num: int) -> "Status1":
        """Create toxic counter - equivalent to STATUS1_TOXIC_TURN(num)"""
        if not 0 <= num <= 15:
            raise ValueError("Toxic counter must be 0-15")
        return cls((num << cls.TOXIC_SHIFT) | cls.TOXIC_POISON)

    @classmethod
    def create_sleep(cls, turns: int) -> "Status1":
        """Factory method for creating sleep status with validation"""
        return cls.sleep_turn(turns)

    @classmethod
    def create_poison(cls) -> "Status1":
        """Factory method for creating regular poison"""
        return cls.POISON

    @classmethod
    def create_toxic(cls, counter: int = 1) -> "Status1":
        """Factory method for creating toxic poison with counter"""
        return cls.toxic_turn(counter)

    @classmethod
    def create_burn(cls) -> "Status1":
        """Factory method for creating burn"""
        return cls.BURN

    @classmethod
    def create_freeze(cls) -> "Status1":
        """Factory method for creating freeze"""
        return cls.FREEZE

    @classmethod
    def create_paralysis(cls) -> "Status1":
        """Factory method for creating paralysis"""
        return cls.PARALYSIS

    # =========================================================================
    # SLEEP COUNTER METHODS
    # =========================================================================

    def get_sleep_turns(self) -> int:
        """Get remaining sleep turns (0-7)"""
        return int(self) & self.SLEEP_MASK

    def set_sleep_turns(self, turns: int) -> "Status1":
        """Set sleep turns and return new Status1"""
        if not 0 <= turns <= 7:
            raise ValueError("Sleep turns must be 0-7")
        return Status1((int(self) & ~self.SLEEP_MASK) | (turns & self.SLEEP_MASK))

    def decrement_sleep(self) -> "Status1":
        """Decrement sleep counter by 1, minimum 0"""
        current = self.get_sleep_turns()
        return self.set_sleep_turns(max(0, current - 1))

    def remove_sleep(self) -> "Status1":
        """Remove sleep status and return new Status1"""
        return Status1(int(self) & ~self.SLEEP_MASK)

    # =========================================================================
    # TOXIC COUNTER METHODS
    # =========================================================================

    def get_toxic_counter(self) -> int:
        """Get toxic poison counter (0-15)"""
        return (int(self) & self.TOXIC_MASK) >> self.TOXIC_SHIFT

    def set_toxic_counter(self, counter: int) -> "Status1":
        """Set toxic counter and return new Status1"""
        if not 0 <= counter <= 15:
            raise ValueError("Toxic counter must be 0-15")
        base = int(self) & ~self.TOXIC_MASK  # Clear toxic counter bits
        return Status1(base | ((counter << self.TOXIC_SHIFT) & self.TOXIC_MASK))

    def increment_toxic_counter(self) -> "Status1":
        """Increment toxic counter by 1, maximum 15"""
        current = self.get_toxic_counter()
        return self.set_toxic_counter(min(15, current + 1))

    # =========================================================================
    # STATUS CHECK METHODS
    # =========================================================================

    def is_asleep(self) -> bool:
        """Check if Pokemon is asleep (has sleep turns > 0)"""
        return self.get_sleep_turns() > 0

    def is_poisoned(self) -> bool:
        """Check if Pokemon has any poison status"""
        return bool(self & self.PSN_ANY)

    def is_badly_poisoned(self) -> bool:
        """Check if Pokemon is badly poisoned (toxic)"""
        return bool(self & self.TOXIC_POISON)

    def is_burned(self) -> bool:
        """Check if Pokemon is burned"""
        return bool(self & self.BURN)

    def is_frozen(self) -> bool:
        """Check if Pokemon is frozen"""
        return bool(self & self.FREEZE)

    def is_paralyzed(self) -> bool:
        """Check if Pokemon is paralyzed"""
        return bool(self & self.PARALYSIS)

    def has_major_status(self) -> bool:
        """Check if Pokemon has any major status condition"""
        return bool(self & self.ANY)

    # =========================================================================
    # STATUS REMOVAL METHODS
    # =========================================================================

    def remove_poison(self) -> "Status1":
        """Remove all poison status and return new Status1"""
        return Status1(int(self) & ~(self.POISON | self.TOXIC_POISON | self.TOXIC_MASK))

    def remove_burn(self) -> "Status1":
        """Remove burn status and return new Status1"""
        return Status1(int(self) & ~self.BURN)

    def remove_freeze(self) -> "Status1":
        """Remove freeze status and return new Status1"""
        return Status1(int(self) & ~self.FREEZE)

    def remove_paralysis(self) -> "Status1":
        """Remove paralysis status and return new Status1"""
        return Status1(int(self) & ~self.PARALYSIS)

    def clear_all(self) -> "Status1":
        """Remove all status conditions and return new Status1"""
        return Status1.NONE


class Status2(IntFlag):
    """Volatile status ailments - from include/constants/battle.h"""

    NONE = 0
    CONFUSION = (1 << 0) | (1 << 1) | (1 << 2)
    FLINCHED = 1 << 3
    UPROAR = (1 << 4) | (1 << 5) | (1 << 6)
    UNUSED = 1 << 7
    BIDE = (1 << 8) | (1 << 9)
    LOCK_CONFUSE = (1 << 10) | (1 << 11)  # e.g. Thrash
    MULTIPLETURNS = 1 << 12
    WRAPPED = (1 << 13) | (1 << 14) | (1 << 15)
    INFATUATION = (1 << 16) | (1 << 17) | (1 << 18) | (1 << 19)  # 4 bits, one for every battler
    FOCUS_ENERGY = 1 << 20
    TRANSFORMED = 1 << 21
    RECHARGE = 1 << 22
    RAGE = 1 << 23
    SUBSTITUTE = 1 << 24
    DESTINY_BOND = 1 << 25
    ESCAPE_PREVENTION = 1 << 26
    NIGHTMARE = 1 << 27
    CURSED = 1 << 28
    FORESIGHT = 1 << 29
    DEFENSE_CURL = 1 << 30
    TORMENT = 1 << 31

    # =========================================================================
    # C MACRO EQUIVALENTS
    # =========================================================================

    # Masks and shifts
    CONFUSION_MASK = 0b111  # 3 bits (0-7)
    UPROAR_MASK = 0b111 << 4  # 3 bits (0-7)
    BIDE_MASK = 0b11 << 8  # 2 bits (0-3)
    LOCK_CONFUSE_MASK = 0b11 << 10  # 2 bits (0-3)
    WRAPPED_MASK = 0b111 << 13  # 3 bits (0-7)
    INFATUATION_MASK = 0b1111 << 16  # 4 bits (0-15)

    CONFUSION_SHIFT = 0
    UPROAR_SHIFT = 4
    BIDE_SHIFT = 8
    LOCK_CONFUSE_SHIFT = 10
    WRAPPED_SHIFT = 13
    INFATUATION_SHIFT = 16

    # =========================================================================
    # C MACRO FACTORY METHODS
    # =========================================================================

    @classmethod
    def confusion_turn(cls, num: int) -> "Status2":
        """Create confusion with turn count - equivalent to STATUS2_CONFUSION_TURN(num)"""
        if not 0 <= num <= 7:
            raise ValueError("Confusion turns must be 0-7")
        return cls(num << cls.CONFUSION_SHIFT)

    @classmethod
    def uproar_turn(cls, num: int) -> "Status2":
        """Create uproar with turn count - equivalent to STATUS2_UPROAR_TURN(num)"""
        if not 0 <= num <= 7:
            raise ValueError("Uproar turns must be 0-7")
        return cls(num << cls.UPROAR_SHIFT)

    @classmethod
    def bide_turn(cls, num: int) -> "Status2":
        """Create bide with turn count - equivalent to STATUS2_BIDE_TURN(num)"""
        if not 0 <= num <= 3:
            raise ValueError("Bide turns must be 0-3")
        return cls(((num << cls.BIDE_SHIFT) & cls.BIDE))

    @classmethod
    def lock_confuse_turn(cls, num: int) -> "Status2":
        """Create lock confuse with turn count - equivalent to STATUS2_LOCK_CONFUSE_TURN(num)"""
        if not 0 <= num <= 3:
            raise ValueError("Lock confuse turns must be 0-3")
        return cls(num << cls.LOCK_CONFUSE_SHIFT)

    @classmethod
    def wrapped_turn(cls, num: int) -> "Status2":
        """Create wrapped with turn count - equivalent to STATUS2_WRAPPED_TURN(num)"""
        if not 0 <= num <= 7:
            raise ValueError("Wrapped turns must be 0-7")
        return cls(num << cls.WRAPPED_SHIFT)

    @classmethod
    def infatuated_with(cls, battler: int) -> "Status2":
        """Create infatuation with specific battler - equivalent to STATUS2_INFATUATED_WITH(battler)"""
        if not 0 <= battler <= 3:
            raise ValueError("Battler must be 0-3")
        # Equivalent to gBitTable[battler] << 16
        return cls((1 << battler) << cls.INFATUATION_SHIFT)

    # =========================================================================
    # CONFUSION COUNTER METHODS
    # =========================================================================

    def get_confusion_turns(self) -> int:
        """Get remaining confusion turns (0-7)"""
        return int(self) & self.CONFUSION_MASK

    def set_confusion_turns(self, turns: int) -> "Status2":
        """Set confusion turns and return new Status2"""
        if not 0 <= turns <= 7:
            raise ValueError("Confusion turns must be 0-7")
        return Status2((int(self) & ~self.CONFUSION_MASK) | (turns & self.CONFUSION_MASK))

    def decrement_confusion(self) -> "Status2":
        """Decrement confusion counter by 1, minimum 0"""
        current = self.get_confusion_turns()
        return self.set_confusion_turns(max(0, current - 1))

    # =========================================================================
    # UPROAR COUNTER METHODS
    # =========================================================================

    def get_uproar_turns(self) -> int:
        """Get remaining uproar turns (0-7)"""
        return (int(self) & self.UPROAR_MASK) >> self.UPROAR_SHIFT

    def set_uproar_turns(self, turns: int) -> "Status2":
        """Set uproar turns and return new Status2"""
        if not 0 <= turns <= 7:
            raise ValueError("Uproar turns must be 0-7")
        return Status2((int(self) & ~self.UPROAR_MASK) | ((turns & 0b111) << self.UPROAR_SHIFT))

    def decrement_uproar(self) -> "Status2":
        """Decrement uproar counter by 1, minimum 0"""
        current = self.get_uproar_turns()
        return self.set_uproar_turns(max(0, current - 1))

    # =========================================================================
    # BIDE COUNTER METHODS
    # =========================================================================

    def get_bide_turns(self) -> int:
        """Get remaining bide turns (0-3)"""
        return (int(self) & self.BIDE_MASK) >> self.BIDE_SHIFT

    def set_bide_turns(self, turns: int) -> "Status2":
        """Set bide turns and return new Status2"""
        if not 0 <= turns <= 3:
            raise ValueError("Bide turns must be 0-3")
        return Status2((int(self) & ~self.BIDE_MASK) | ((turns & 0b11) << self.BIDE_SHIFT))

    def decrement_bide(self) -> "Status2":
        """Decrement bide counter by 1, minimum 0"""
        current = self.get_bide_turns()
        return self.set_bide_turns(max(0, current - 1))

    # =========================================================================
    # LOCK/CONFUSE (THRASH) COUNTER METHODS
    # =========================================================================

    def get_lock_confuse_turns(self) -> int:
        """Get remaining thrash/outrage/etc turns (0-3)"""
        return (int(self) & self.LOCK_CONFUSE_MASK) >> self.LOCK_CONFUSE_SHIFT

    def set_lock_confuse_turns(self, turns: int) -> "Status2":
        """Set lock confuse turns and return new Status2"""
        if not 0 <= turns <= 3:
            raise ValueError("Lock confuse turns must be 0-3")
        return Status2((int(self) & ~self.LOCK_CONFUSE_MASK) | ((turns & 0b11) << self.LOCK_CONFUSE_SHIFT))

    def decrement_lock_confuse(self) -> "Status2":
        """Decrement lock confuse counter by 1, minimum 0"""
        current = self.get_lock_confuse_turns()
        return self.set_lock_confuse_turns(max(0, current - 1))

    # =========================================================================
    # WRAPPED COUNTER METHODS
    # =========================================================================

    def get_wrapped_turns(self) -> int:
        """Get remaining wrapped turns (0-7)"""
        return (int(self) & self.WRAPPED_MASK) >> self.WRAPPED_SHIFT

    def set_wrapped_turns(self, turns: int) -> "Status2":
        """Set wrapped turns and return new Status2"""
        if not 0 <= turns <= 7:
            raise ValueError("Wrapped turns must be 0-7")
        return Status2((int(self) & ~self.WRAPPED_MASK) | ((turns & 0b111) << self.WRAPPED_SHIFT))

    def decrement_wrapped(self) -> "Status2":
        """Decrement wrapped counter by 1, minimum 0"""
        current = self.get_wrapped_turns()
        return self.set_wrapped_turns(max(0, current - 1))

    # =========================================================================
    # INFATUATION METHODS (4 bits, one per battler)
    # =========================================================================

    def get_infatuation_mask(self) -> int:
        """Get infatuation bitmask (0-15, one bit per battler)"""
        return (int(self) & self.INFATUATION_MASK) >> self.INFATUATION_SHIFT

    def set_infatuation_mask(self, mask: int) -> "Status2":
        """Set infatuation bitmask and return new Status2"""
        if not 0 <= mask <= 15:
            raise ValueError("Infatuation mask must be 0-15")
        return Status2((int(self) & ~self.INFATUATION_MASK) | ((mask & 0xF) << self.INFATUATION_SHIFT))

    def is_infatuated_with(self, battler_id: int) -> bool:
        """Check if infatuated with specific battler (0-3)"""
        if not 0 <= battler_id <= 3:
            raise ValueError("Battler ID must be 0-3")
        mask = self.get_infatuation_mask()
        return bool(mask & (1 << battler_id))

    def set_infatuated_with(self, battler_id: int) -> "Status2":
        """Set infatuation with specific battler and return new Status2"""
        if not 0 <= battler_id <= 3:
            raise ValueError("Battler ID must be 0-3")
        mask = self.get_infatuation_mask()
        return self.set_infatuation_mask(mask | (1 << battler_id))

    def remove_infatuation_with(self, battler_id: int) -> "Status2":
        """Remove infatuation with specific battler and return new Status2"""
        if not 0 <= battler_id <= 3:
            raise ValueError("Battler ID must be 0-3")
        mask = self.get_infatuation_mask()
        return self.set_infatuation_mask(mask & ~(1 << battler_id))

    def get_infatuation_battlers(self) -> set[int]:
        """Get set of battlers this Pokemon is infatuated with"""
        infatuation_bits = self.get_infatuation_mask()
        return {i for i in range(4) if infatuation_bits & (1 << i)}

    def is_infatuated_with_battler(self, battler: int) -> bool:
        """Check if infatuated with specific battler using factory method"""
        if not 0 <= battler <= 3:
            return False
        return bool(self & self.infatuated_with(battler))

    # =========================================================================
    # STATUS CHECK METHODS
    # =========================================================================

    def is_confused(self) -> bool:
        """Check if Pokemon is confused (has confusion turns > 0)"""
        return self.get_confusion_turns() > 0

    def is_flinched(self) -> bool:
        """Check if Pokemon flinched this turn"""
        return bool(self & self.FLINCHED)

    def is_in_uproar(self) -> bool:
        """Check if Pokemon is in uproar (has uproar turns > 0)"""
        return self.get_uproar_turns() > 0

    def is_using_bide(self) -> bool:
        """Check if Pokemon is using bide (has bide turns > 0)"""
        return self.get_bide_turns() > 0

    def is_lock_confused(self) -> bool:
        """Check if Pokemon is locked into thrash/outrage (has turns > 0)"""
        return self.get_lock_confuse_turns() > 0

    def is_wrapped(self) -> bool:
        """Check if Pokemon is wrapped (has wrapped turns > 0)"""
        return self.get_wrapped_turns() > 0

    def is_infatuated(self) -> bool:
        """Check if Pokemon is infatuated with any battler"""
        return self.get_infatuation_mask() > 0

    def has_focus_energy(self) -> bool:
        """Check if Pokemon has Focus Energy active"""
        return bool(self & self.FOCUS_ENERGY)

    def is_transformed(self) -> bool:
        """Check if Pokemon is transformed"""
        return bool(self & self.TRANSFORMED)

    def must_recharge(self) -> bool:
        """Check if Pokemon must recharge this turn"""
        return bool(self & self.RECHARGE)

    def is_raging(self) -> bool:
        """Check if Pokemon is in rage"""
        return bool(self & self.RAGE)

    def has_substitute(self) -> bool:
        """Check if Pokemon has a substitute"""
        return bool(self & self.SUBSTITUTE)

    def has_destiny_bond(self) -> bool:
        """Check if Pokemon has Destiny Bond active"""
        return bool(self & self.DESTINY_BOND)

    def cannot_escape(self) -> bool:
        """Check if Pokemon cannot escape"""
        return bool(self & self.ESCAPE_PREVENTION)

    def has_nightmare(self) -> bool:
        """Check if Pokemon has nightmare"""
        return bool(self & self.NIGHTMARE)

    def is_cursed(self) -> bool:
        """Check if Pokemon is cursed"""
        return bool(self & self.CURSED)

    def has_foresight(self) -> bool:
        """Check if Pokemon is affected by foresight"""
        return bool(self & self.FORESIGHT)

    def used_defense_curl(self) -> bool:
        """Check if Pokemon used Defense Curl (for Rollout boost)"""
        return bool(self & self.DEFENSE_CURL)

    def is_tormented(self) -> bool:
        """Check if Pokemon is tormented"""
        return bool(self & self.TORMENT)

    # =========================================================================
    # STATUS REMOVAL METHODS
    # =========================================================================

    def remove_confusion(self) -> "Status2":
        """Remove confusion status and return new Status2"""
        return Status2(int(self) & ~self.CONFUSION_MASK)

    def remove_flinch(self) -> "Status2":
        """Remove flinch status and return new Status2"""
        return Status2(int(self) & ~self.FLINCHED)

    def remove_uproar(self) -> "Status2":
        """Remove uproar status and return new Status2"""
        return Status2(int(self) & ~self.UPROAR_MASK)

    def remove_bide(self) -> "Status2":
        """Remove bide status and return new Status2"""
        return Status2(int(self) & ~self.BIDE_MASK)

    def remove_lock_confuse(self) -> "Status2":
        """Remove lock confuse status and return new Status2"""
        return Status2(int(self) & ~self.LOCK_CONFUSE_MASK)

    def remove_wrapped(self) -> "Status2":
        """Remove wrapped status and return new Status2"""
        return Status2(int(self) & ~self.WRAPPED_MASK)

    def remove_all_infatuation(self) -> "Status2":
        """Remove all infatuation and return new Status2"""
        return Status2(int(self) & ~self.INFATUATION_MASK)

    def clear_turn_flags(self) -> "Status2":
        """Clear turn-based flags (flinch, recharge, destiny bond) and return new Status2"""
        return Status2(int(self) & ~(self.FLINCHED | self.RECHARGE | self.DESTINY_BOND))

    def clear_all(self) -> "Status2":
        """Remove all status conditions and return new Status2"""
        return Status2.NONE
