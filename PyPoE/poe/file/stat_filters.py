"""
Parser for skillpopup_stat_filters.txt

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/poe/file/stat_filters.py                                   |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

Parser for Metadata/StatDescriptions/skillpopup_stat_filters.txt

Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

Public API
-------------------------------------------------------------------------------

.. autoclass:: StatFilterFile

.. autoclass:: SkillEntry
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import re

from PyPoE.poe.file.shared import AbstractFileReadOnly

# self
from PyPoE.shared.mixins import ReprMixin

# 3rd-party


# =============================================================================
# Globals
# =============================================================================

__all__ = []

# =============================================================================
# Classes
# =============================================================================


class SkillEntry(ReprMixin):
    """

    Attributes
    ----------
    skill_id : str
        Id from ActiveSkills.dat
    translation_file_path : str
        Path to the translation file that should be used for this skill id.
        Path is relative to content.ggpk
    stats : list[str]
        Order in which to display stats
    entries : list[str]
        The section's lines as written: description names, and `$<group>` where
        the section pulls in a group (`stats` holds the same with groups expanded)
    """

    __slots__ = ["skill_id", "translation_file_path", "stats", "entries"]

    def __init__(self, skill_id, translation_file_path, stats, entries=None):
        self.skill_id = skill_id
        self.translation_file_path = translation_file_path
        self.stats = stats
        self.entries = entries if entries is not None else list(stats)


class StatFilterFile(AbstractFileReadOnly):
    """
    Parser for Metadata/skillpopup_stat_filters.txt

    Attributes
    ----------
    groups : dict[str, list[str]]
        Dictionary containing stat groups with the id as key, and the list of
        stats as value
    skills : dict[str, SkillEntry]
        Dictionary mapping the active skill id (as key) to a the respective
        :class:`SkillEntry` instance as value.
    """

    _re_find_sections = re.compile(
        # header
        # A few headers carry two spaces before the file (`phase_run  "..."`).
        r"^(?:" r"group (?P<group>[\w]+)|" r'(?P<skill_id>[\w]+)[ \t]+"(?P<file>[\w/\.]+)"' r")[ \t]*[\r\n]+"
        # contents
        r"^{" r"(?P<contents>[^}]*)" r"^}",
        re.UNICODE | re.MULTILINE,
    )

    # `copy <skill id> <source skill id>`: the skill reads the source's file and stats.
    _re_find_copies = re.compile(
        r"^copy[ \t]+(?P<skill_id>[\w]+)[ \t]+(?P<source_id>[\w]+)[ \t]*\r?$",
        re.UNICODE | re.MULTILINE,
    )

    _re_find_contents = re.compile(
        r"[\w$]+",
        re.UNICODE | re.MULTILINE,
    )

    groups = None
    skills = None

    def _read(self, buffer, *args, **kwargs):
        data = buffer.read().decode("utf-16")

        self.groups = {}
        self.skills = {}

        for match in self._re_find_sections.finditer(data):
            contents = self._re_find_contents.findall(match.group("contents"))
            if match.group("group"):
                self.groups[match.group("group")] = contents
            elif match.group("skill_id"):
                stats = []
                for stat in contents:
                    if stat.startswith("$"):
                        stats.extend(self.groups[stat[1:]])
                    else:
                        stats.append(stat)
                self.skills[match.group("skill_id")] = SkillEntry(
                    skill_id=match.group("skill_id"),
                    translation_file_path=match.group("file"),
                    stats=stats,
                    entries=contents,
                )

        # Copies resolve after every section is read: a source may be defined later in
        # the file, or be a copy itself. A copy never replaces a skill with its own section.
        copies = {m.group("skill_id"): m.group("source_id") for m in self._re_find_copies.finditer(data)}
        pending = {k: v for k, v in copies.items() if k not in self.skills}
        while pending:
            resolved = [k for k, v in pending.items() if v in self.skills]
            if not resolved:
                break
            for skill_id in resolved:
                source = self.skills[pending.pop(skill_id)]
                self.skills[skill_id] = SkillEntry(
                    skill_id=skill_id,
                    translation_file_path=source.translation_file_path,
                    stats=list(source.stats),
                    entries=list(source.entries),
                )
