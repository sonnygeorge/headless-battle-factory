import os
from functools import lru_cache
from typing import List

from src.battle_factory.enums.species import Species
from src.battle_factory.data.species_weights_table import get_weight_hg_by_species


def get_weight_hg(species: Species) -> int:
    """Get species weight in hectograms using internal Species enum index.

    Raises RuntimeError if species id is out of bounds.
    """
    return get_weight_hg_by_species(int(species))
