"""Public organizer modes mapped onto the existing legacy router."""
VISITS="Por período ou data"
WEEKLY="Calendário inteligente"
FULL="Calendário completo"
GROUPS="Viagens agrupadas"


def organizer_mode(legacy, stage):
    if legacy in (WEEKLY,FULL):
        return "Calendário"
    if legacy==GROUPS and stage=="França":
        return GROUPS
    return "Visitas"


def legacy_mode(mode, stage, calendar_layout="Semanal"):
    if mode=="Calendário":
        return FULL if calendar_layout=="Completo" else WEEKLY
    if mode==GROUPS and stage=="França":
        return GROUPS
    return VISITS
