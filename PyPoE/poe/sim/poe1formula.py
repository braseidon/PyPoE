"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/sim/poe1formula.py                                     |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Formulas for calculating certain things.

Agreement
===============================================================================

See PyPoE/LICENSE


.. todo::

  Find out the real function for calculating the stat requirement.

Documentation
===============================================================================

.. autoclass:: GemTypes

.. autofunction:: armour_damage_reduction

.. autofunction:: chance_to_hit

.. autofunction:: chance_to_evade

.. autofunction:: gem_stat_requirement
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import math
from enum import Enum

# self

# =============================================================================
# Globals
# =============================================================================

__all__ = ["GemTypes", "gem_stat_requirement"]

# =============================================================================
# Classes
# =============================================================================


class GemTypes(Enum):
    """
    Attributes
    ----------
    support
        Support Skill Gem
    active
        Active Skill Gem
    """

    support = 1
    active = 2


# =============================================================================
# Functions
# =============================================================================


def armour_damage_reduction(armour, damage):
    """
    Calculates the damage reduction from armour.

    .. note::

        The final damage reduction may differ; there are other stats that can
        grant damage reduction and damage reduction is capped.

    Parameters
    ----------
    armour : int
        Armour value of the defender
    damage : int
        Physical damage of the attacker's hit before mitigation

    Returns
    -------
    int
        damage reduction factor
    """
    return armour / (armour + 10 * damage)


def chance_to_hit(accuracy, evasion):
    """
    Calculates the chance to hit for the given accuracy and evasion.

    Parameters
    ----------
    accuracy : int
        Accuracy rating of the attacker
    evasion : int
        Evasion rating of the defender

    Returns
    -------
    float
        chance to hit
    """
    return accuracy / (accuracy + (evasion * 0.25) ** 0.8)


def chance_to_evade(accuracy, evasion):
    """
    Calculates the chance to evade for the given accuracy and evasion.

    Parameters
    ----------
    accuracy : int
        Accuracy rating of the attacker
    evasion : int
        Evasion rating of the defender

    Returns
    -------
    float
        chance to evade
    """
    return 1 - chance_to_hit(accuracy, evasion)


def gem_stat_requirement(level, gtype=GemTypes.support, multi=100):
    """
    Calculates and returns the stat requirement for the specified level
    requirement.

    A single closed form covers every gem type and every multiplier::

        (20 + (level - 3) * 3) * (multi / 100) ** 0.9 * stat_type

    where ``stat_type`` is 0.7 for active gems and 0.5 for support gems. The
    result is rounded half up (the game rounds half up, not half to even).
    Any multiplier is accepted, not just the values present in SkillGems.dat.

    Requirements below 14 return 0, matching the game's display rule.


    .. warning::
        This formula is reverse engineered and may break with game updates.

    Parameters
    ----------
    level : int
        Level requirement for the current gem level
    gtype : GemTypes
        Type of the gem; i.e. GemTypes.support or GemTypes.active
    multi : int
        Stat multiplier, i.e. from SkillGems.dat


    Returns
    -------
    int
        calculated stat requirement


    Raises
    ------
    ValueError
        if gtype is invalid
    """
    if gtype == GemTypes.active:
        stat_type = 0.7
    elif gtype == GemTypes.support:
        stat_type = 0.5
    else:
        raise ValueError("Invalid gtype '%s'. Valid types are:\n%s" % (gtype, GemTypes))

    if level is None:
        return 0
    value = (20 + (level - 3) * 3) * (multi / 100) ** 0.9 * stat_type
    # Round half up (the game rounds half up, not Python's round-half-to-even).
    result = math.floor(value + 0.5)
    # Attribute requirements lower then 14 are not displayed in game.
    # TODO: Would it be more appropriate to output the result as-is and
    #       handle display on the wiki side?
    return 0 if result < 14 else result
