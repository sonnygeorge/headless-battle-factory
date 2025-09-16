from enum import IntEnum, IntFlag


class Weather(IntEnum):
    NONE = 0
    SUN = 1
    RAIN = 2
    SANDSTORM = 3
    HAIL = 4


class KnockedOffTracker(IntFlag):
    """Tracks which Pokemon had items knocked off per side - from pokeemerald/include/battle.h"""

    NONE = 0
    MON_0 = 1 << 0  # Party slot 0
    MON_1 = 1 << 1  # Party slot 1
    MON_2 = 1 << 2  # Party slot 2
    MON_3 = 1 << 3  # Party slot 3
    MON_4 = 1 << 4  # Party slot 4
    MON_5 = 1 << 5  # Party slot 5

    # =========================================================================
    # KNOCK OFF STATUS CHECK METHODS
    # =========================================================================

    def is_knocked_off(self, slot: int) -> bool:
        """Check if Pokemon in party slot had item knocked off (0-5)"""
        if not 0 <= slot <= 5:
            raise ValueError("Party slot must be 0-5")
        return bool(self & (1 << slot))

    def any_knocked_off(self) -> bool:
        """Check if any Pokemon on this side had items knocked off"""
        return int(self) > 0

    def count_knocked_off(self) -> int:
        """Count how many Pokemon had items knocked off"""
        return bin(int(self)).count("1")

    def get_knocked_off_slots(self) -> list[int]:
        """Get list of party slots that had items knocked off"""
        return [slot for slot in range(6) if self.is_knocked_off(slot)]

    # =========================================================================
    # KNOCK OFF STATUS MODIFICATION METHODS
    # =========================================================================

    def set_knocked_off(self, slot: int) -> "KnockedOffTracker":
        """Mark Pokemon in party slot as having item knocked off"""
        if not 0 <= slot <= 5:
            raise ValueError("Party slot must be 0-5")
        return KnockedOffTracker(int(self) | (1 << slot))

    def clear_knocked_off(self, slot: int) -> "KnockedOffTracker":
        """Clear knocked off status for Pokemon in party slot"""
        if not 0 <= slot <= 5:
            raise ValueError("Party slot must be 0-5")
        return KnockedOffTracker(int(self) & ~(1 << slot))

    def set_multiple_knocked_off(self, slots: list[int]) -> "KnockedOffTracker":
        """Mark multiple Pokemon as having items knocked off"""
        result = int(self)
        for slot in slots:
            if not 0 <= slot <= 5:
                raise ValueError(f"Party slot {slot} must be 0-5")
            result |= 1 << slot
        return KnockedOffTracker(result)

    def clear_multiple_knocked_off(self, slots: list[int]) -> "KnockedOffTracker":
        """Clear knocked off status for multiple Pokemon"""
        result = int(self)
        for slot in slots:
            if not 0 <= slot <= 5:
                raise ValueError(f"Party slot {slot} must be 0-5")
            result &= ~(1 << slot)
        return KnockedOffTracker(result)

    def clear_all(self) -> "KnockedOffTracker":
        """Clear all knocked off status (e.g., at end of battle)"""
        return KnockedOffTracker.NONE

    def toggle_knocked_off(self, slot: int) -> "KnockedOffTracker":
        """Toggle knocked off status for Pokemon in party slot"""
        if not 0 <= slot <= 5:
            raise ValueError("Party slot must be 0-5")
        return KnockedOffTracker(int(self) ^ (1 << slot))


class GrowthRate(IntEnum):
    """Experience growth rates - from include/constants/pokemon.h"""

    MEDIUM_FAST = 0
    ERRATIC = 1
    FLUCTUATING = 2
    MEDIUM_SLOW = 3
    FAST = 4
    SLOW = 5


class EggGroup(IntEnum):
    """Pokemon egg groups - from include/constants/pokemon.h"""

    NONE = 0
    MONSTER = 1
    WATER_1 = 2
    BUG = 3
    FLYING = 4
    FIELD = 5
    FAIRY = 6
    GRASS = 7
    HUMAN_LIKE = 8
    WATER_3 = 9
    MINERAL = 10
    AMORPHOUS = 11
    WATER_2 = 12
    DITTO = 13
    DRAGON = 14
    NO_EGGS_DISCOVERED = 15


class BodyColor(IntEnum):
    """Body colors for Pokédex search - from include/constants/pokemon.h"""

    RED = 0
    BLUE = 1
    YELLOW = 2
    GREEN = 3
    BLACK = 4
    BROWN = 5
    PURPLE = 6
    GRAY = 7
    WHITE = 8
    PINK = 9
