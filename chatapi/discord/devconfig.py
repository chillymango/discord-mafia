"""
Use the same config for all games
"""

CONFIG = {
    "roles": {
        "Godfather": {
            "night_immune": True,
            "rb_immune": True,
            "target_immune": False,
            "detect_immune": True,
        },
        "Lookout": {
            "allow_self_target": True,
        },
        "SerialKiller": {
            "intercept_rb": True,
            "rb_immune": True,
            "night_immune": True,
            "detect_immune": True,
        }
    },
    "turns": {
        # these are minimum lengths, if there are lots of things to print, we'll go longer
        "phase_lengths": {
            "daybreak": 10.0,
            "daylight": 180.0,
            "dusk": 10.0,
            "night": 30.0,
            "night_sequence": 5.0,
        }
    },
    "setup": {
        # assume we'll have 15 players (fill with bots if needed)
        "role_list": [
            "RoleGroup::TownGovernment",
            "RoleGroup::TownInvestigative",
            "RoleGroup::TownProtective",
            "RoleGroup::TownKilling",
            "RoleGroup::TownPower",
            "RoleGroup::TownSupport",
            "RoleGroup::TownRandom",
            "RoleGroup::TownRandom",
            "RoleName::Godfather",
            "RoleGroup::MafiaRandom",
            "RoleGroup::MafiaRandom",
            "RoleName::SerialKiller",
            "RoleName::Jester",
            "RoleName::Survivor",
            "RoleName::AnyRandom",
        ],
        # scalings for odds in RoleGroup selections
        # if the role is not listed, it's assumed to be 0
        "role_weights": {
            # Town Roles
            "Doctor": 0.3,
            "Escort": 0.5,
            "Lookout": 0.2,
            "Consort": 0.3,

            # Mafia Roles
            "GodFather": 0.0,

            # Triad Roles

            # Neutral Roles

        }
    }
}