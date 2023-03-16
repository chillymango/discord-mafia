"""
Preferred Role and Blocked Role
"""

from datetime import datetime
import json
import time
import typing as T

import disnake

from chatapi.discord.router import router
from engine.role import NAME_TO_ROLE


async def submit_role_pref_modal(interaction: "disnake.Interaction") -> None:
    import pdb; pdb.set_trace()


ROLE_PREF_MODAL = None

def role_pref_modal() -> disnake.ui.Modal:
    """
    Select a preferred role and/or a blocked role
    """
    global ROLE_PREF_MODAL
    if ROLE_PREF_MODAL is not None:
        return ROLE_PREF_MODAL

    preferred_role_row = disnake.ui.ActionRow()
    preferred_role_row.add_string_select(
        custom_id="preferred-role-id",
        options=list(NAME_TO_ROLE.keys()),
    )

    blocked_role_row = disnake.ui.ActionRow()
    blocked_role_row.add_string_select(
        custom_id="blocked-role-id",
        options=list(NAME_TO_ROLE.keys()),
    )

    modal = disnake.ui.Modal(
        title="Role Preferences",
        custom_id=f"role-pref-modal",
        components=[preferred_role_row, blocked_role_row],
    )

    router.register_custom_modal_callback("bug-report-modal", submit_role_pref_modal)

    ROLE_PREF_MODAL = modal
    return modal
