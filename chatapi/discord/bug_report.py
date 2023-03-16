"""
Bug Report Modal
"""
from datetime import datetime
import json
import time
import typing as T

import disnake

from chatapi.discord.router import router


async def submit_report_callback(interaction: "disnake.ModalInteraction") -> None:
    report_role = None
    report_text = None
    for row in interaction.data.components:
        for entry in row['components']:
            if entry.get('custom_id') == 'bug-report-role':
                report_role = entry['value']
            elif entry.get('custom_id') == 'bug-report-text':
                report_text = entry['value']
    
    with open(f"bugs\\bug_report_{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}.log", "w+") as bugfile:
        json.dump(dict(report_role=report_role, report_text=report_text), bugfile)

    await interaction.send('Issued Report Successfully', ephemeral=True)


BUG_REPORT_MODAL = None

def bug_report_modal() -> disnake.ui.Modal:
    """
    Create a Bug Report
    """
    global BUG_REPORT_MODAL
    if BUG_REPORT_MODAL is not None:
        return BUG_REPORT_MODAL

    modal = disnake.ui.Modal(
        title="Crier Statement",
        custom_id=f"bug-report-modal",
        components=[],
    )
    modal.add_text_input(
        label="Game Role",
        custom_id="bug-report-role",
        style=disnake.TextInputStyle.short,
        required=True,
        placeholder="Fill out your role"
    )
    modal.add_text_input(
        label="Bug Report (please include as much detail as possible)",
        custom_id="bug-report-text",
        style=disnake.TextInputStyle.long,
        required=True,
        placeholder="Fill out the bug description here"
    )

    router.register_custom_modal_callback("bug-report-modal", submit_report_callback)

    BUG_REPORT_MODAL = modal
    return modal
