"""DATA24CDE: descriptive D-004 evidence, not a finalist selection.

No live Drive, UI, private state, new observations or scoring. Explicitly named
candidates and the separate five-base study are not official finalists.
"""
from __future__ import annotations

from copy import deepcopy
from base_research_expanded_model import observed_housing
from housing_short_stay_research_model import housing_research_overview
from city_research_round2 import load_round2
from city_research_packs_model import load_city_packs
from city_market import load_market
from city_profiles_model import load_profiles
from data_model import load_data
from data25_priority_rail_model import RESEARCH_BASE_IDS, RESEARCH_SCOPE_APPROVED_AT


# Transcription reviewed against data/trip.json snapshot 2026-11-14.
# This is a historical candidate reference, not the owner's finalist decision.
# Changing the free-text note cannot add or remove IDs. Review explicitly when
# the source changes; do not silently reinterpret the note.
D004_SNAPSHOT_CANDIDATES = ("metz", "mulhouse", "nancy", "strasbourg")
D004_CANDIDATES_REFERENCE_DATE = "2026-11-14"


def validate_scope_coverage(ids, sources):
    for source, available in sources.items():
        missing = sorted(set(ids) - set(available))
        if missing:
            raise ValueError(f"D-004: IDs ausentes em {source}: {', '.join(missing)}")


def scope_for_d004(snapshot, research, five):
    decision = next(d for d in snapshot["decisions"] if d["id"] == "D-004")
    # Explicit reviewed reference, never a parser of the decision's prose.
    named = sorted(D004_SNAPSHOT_CANDIDATES)
    historical = sorted(five["base_ids"])
    validate_scope_coverage(named + historical + list(RESEARCH_BASE_IDS), {
        "pesquisa ampliada": {c["id"] for c in research["cities"]},
    })
    if len(historical) != len(set(historical)):
        raise ValueError("D-004: IDs duplicados no estudo de cinco bases")
    shortlist = sorted(c["id"] for c in research["cities"] if c["shortlist"])
    return {
        "decision_id": "D-004", "decision_status": decision["status"],
        "snapshot_date": snapshot["snapshot_date"],
        "snapshot_source": "data/trip.json",
        "official_source_url": snapshot["sources"]["decisions"],
        "snapshot_note": decision.get("note"),
        "named_candidates": named,
        "named_candidates_reference_date": D004_CANDIDATES_REFERENCE_DATE,
        "named_candidates_source": "reviewed D004_SNAPSHOT_CANDIDATES constant; historical snapshot",
        "five_base_study_ids": historical,
        "five_base_study_source": "data/five_base_comparison_evidence_2026_11.json",
        "five_base_study_date": five["checked_at"],
        "five_base_study_window": deepcopy(five["research_window"]),
        "historical_shortlist_ids": shortlist,
        "historical_shortlist_source": "data/base_city_research_expanded_2026_11.json",
        "historical_shortlist_date": research["retrieved_at"],
        "official_finalist_ids": None,
        "approved_research_base_ids": list(RESEARCH_BASE_IDS),
        "research_scope_approved_at": RESEARCH_SCOPE_APPROVED_AT,
        "status": "scope_unconfirmed",
        "descriptive_ids": sorted(set(named) | set(historical)),
        "priority_assignment": None,
    }


def coworking_state(observation):
    # Same three-valued evidence as UX113, without importing Streamlit.
    value = (observation or {}).get("late_work_compatible")
    return ("compatible_2026" if value is True else
            "incompatible_2026" if value is False else "indeterminate")


def project_living_evidence(*, snapshot, research, five, round2, packs, market, profiles):
    """D-004 non-rail evidence, independent of the railway matrix."""
    scope = scope_for_d004(snapshot, research, five)
    by_city = {c["id"]: c for c in research["cities"]}
    costs = {c["id"]: c for c in round2["cities"]}
    pack_rows = {c["city_id"]: c for c in packs["cities"]}
    market_rows = {c["id"]: c for c in market["cities"]}
    profile_rows = {c["city_id"]: c for c in profiles["cities"]}
    housing_overview = {c["base_id"]: c for c in
                        housing_research_overview(research=research)["bases"]}
    validate_scope_coverage(scope["descriptive_ids"], {
        "pesquisa ampliada": by_city,
        "visão de moradia": housing_overview,
    })
    rows = []
    for ident in scope["descriptive_ids"]:
        city = by_city[ident]
        cost = costs.get(ident) or {}
        pack = pack_rows.get(ident) or {}
        local = market_rows.get(ident) or {}
        profile = profile_rows.get(ident) or {}
        coworking = cost.get("coworking")
        daily = pack.get("daily_life") or {}
        climate = pack.get("climate") or {}
        restaurant = daily.get("restaurant_two_midrange_eur_2026")
        # Keep the original source modalities; never add pack and canonical
        # copies of the same offers, or add monthly prices into a season quote.
        observed = observed_housing(city)
        overview = housing_overview[ident]
        rows.append({
            "id": ident, "name": city["name"], "country": city["country"],
            "named_in_snapshot": ident in scope["named_candidates"],
            "in_five_base_study": ident in scope["five_base_study_ids"],
            "housing": {
                "summary": observed, "overview": overview,
                "historical_offers": city["housing_offers"],
                "market_sample_separate_not_additive": local.get("offers"),
                "neighborhoods": pack.get("neighborhoods"),
                "requirements": research.get("rental_requirements"),
                "target_nights": research.get("target_nights"),
                "travelers": research["travelers"],
                "total_2027": None, "deposit_2027": None,
                "contract_2027_verified": None,
                "source_dataset": "data/base_city_research_expanded_2026_11.json",
                "source_date": research["retrieved_at"],
                "market_source_date": market["checked_at"] if local else None,
                "neighborhood_source_date": packs["checked_at"] if pack else None,
            },
            "daily_life": {
                "restaurant_eur_two": restaurant,
                "restaurant_source_url": daily.get("restaurant_source_url"),
                "restaurant_basis": daily.get("restaurant_basis"),
                "restaurant_source_date": packs["checked_at"] if restaurant is not None else None,
                "urban_pass": local.get("urban_pass"),
                "urban_pass_source_date": market["checked_at"] if local else None,
                "comparable_local_basket_eur": daily.get("complete_comparable_basket_eur"),
                "local_grocery_basket_eur": daily.get("grocery_basket_eur"),
                "climate": climate or None,
                "profile_evidence": [e for e in profile.get("evidence", [])
                                     if e["section"] in ("transport", "daily_costs",
                                                        "climate", "quality_of_life")],
            },
            "remote_work": {
                "coworking": coworking,
                "pack_reference": (pack.get("remote_work") or {}).get("coworking_reference"),
                "coworking_source_date": round2["checked_at"] if coworking else None,
                "compatibility_2026": coworking_state(coworking),
                "compatibility_2027": "indeterminate",
                "residential_internet_verified": overview["verified_internet"],
                "residential_internet_2027": None,
                "profile_evidence": [e for e in profile.get("evidence", [])
                                     if e["section"] == "remote_work"],
            },
            "decision_evidence": {
                "housing_quotes": "not_confirmed",
                "comparable_local_basket": "documented" if daily.get("complete_comparable_basket_eur") is not None else "unknown",
                "remote_work_access_2027": "unknown",
                "climate_normals": "documented_context" if climate.get("months_9_10_11") is not None else "unknown",
                "research_priority": None,
            },
        })
    for row in rows:
        row["research_gaps"] = living_research_gaps(row)
    counts = living_counts(rows)
    return deepcopy({
        "scope": scope, "rows": rows, "counts": counts,
        "shared_budget_context_not_local": market["common_costs"],
        "shared_legal_reference": market.get("legal"),
        "round2_common_sources": round2["common_sources"],
        "read_only": True, "official_plan_modified": False,
    })


def living_counts(rows):
    """Canonical D-004 counts for the audited scope or an exact subset."""
    return {
        "bases": len(rows),
        "with_historical_housing": sum(r["housing"]["summary"]["count"] > 0 for r in rows),
        "with_three_verified_quotes": sum(r["housing"]["overview"]["available_for_56_to_60_nights_2027"] >= 3 for r in rows),
        "with_restaurant": sum(r["daily_life"]["restaurant_eur_two"] is not None for r in rows),
        "with_urban_pass": sum(r["daily_life"]["urban_pass"] is not None for r in rows),
        "with_local_basket": sum(r["daily_life"]["comparable_local_basket_eur"] is not None for r in rows),
        "with_climate": sum((r["daily_life"]["climate"] or {}).get("months_9_10_11") is not None for r in rows),
        "with_coworking": sum(r["remote_work"]["coworking"] is not None for r in rows),
        "with_residential_internet": sum(r["remote_work"]["residential_internet_2027"] is True for r in rows),
    }


def project_d004(*, snapshot, research, five, round2, packs, market, profiles,
                 rail_by_base):
    result = project_living_evidence(snapshot=snapshot, research=research, five=five,
                                    round2=round2, packs=packs, market=market, profiles=profiles)
    validate_scope_coverage(result["scope"]["descriptive_ids"], {
        "cobertura ferroviária DATA24A": rail_by_base,
    })
    for row in result["rows"]:
        row["rail"] = deepcopy(rail_by_base[row["id"]])
        row["decision_evidence"]["return_and_door_to_door_2027"] = "not_confirmed"
        row["research_gaps"] = research_gaps(row)
    return result


def living_research_gaps(row):
    """Classify non-rail evidence needs; no ranking or official priority."""
    h, d, w = (row[k] for k in ("housing", "daily_life", "remote_work"))
    blockers, complementary, context = [], [], []
    if h["overview"]["available_for_56_to_60_nights_2027"] < 3:
        blockers.append("três cotações comparáveis de 2027")
    if h["summary"]["count"] < 3:
        complementary.append("ampliar amostra histórica de moradia")
    else:
        context.append("amostra histórica de moradia")
    if w["residential_internet_2027"] is not True:
        blockers.append("internet no imóvel")
    if w["compatibility_2027"] != "compatible":
        if w["compatibility_2026"] == "incompatible_2026":
            blockers.append("alternativa de coworking para expediente completo")
        elif not w["coworking"]:
            blockers.append("pesquisar coworking e condições de acesso")
        else:
            blockers.append("confirmar acesso de coworking no expediente")
    if d["comparable_local_basket_eur"] is None:
        blockers.append("cesta local comparável")
    if d["urban_pass"] is None:
        blockers.append("tarifa e condições do transporte urbano")
    else:
        blockers.append("validar passe urbano para 2027")
        context.append("passe urbano histórico")
    if d["restaurant_eur_two"] is None:
        complementary.append("restaurante para dois")
    else:
        context.append("restaurante histórico")
    if (d["climate"] or {}).get("months_9_10_11") is None:
        complementary.append("normais climáticas")
    else:
        context.append("normais climáticas")
    return {"decision_blockers": blockers, "complementary": complementary,
            "sufficient_for_context_only": context}


def research_gaps(row):
    """Retain the historical full-audit gap ordering and railway semantics."""
    result = living_research_gaps(row)
    rail = row["rail"]
    blockers = result["decision_blockers"]
    if rail["missing"]:
        blockers.append(f"tempos ausentes ({rail['missing']}/{rail['eligible']}) — validar destinos relevantes")
    blockers.append("retorno e porta a porta nos destinos relevantes")
    return result


def build_living_evidence(research, five):
    return project_living_evidence(snapshot=load_data(), research=research, five=five,
                                   round2=load_round2(), packs=load_city_packs(),
                                   market=load_market(), profiles=load_profiles(canonical=research))


def build_d004_audit(research, five, rail_by_base):
    return project_d004(snapshot=load_data(), research=research, five=five,
                        round2=load_round2(), packs=load_city_packs(),
                        market=load_market(), profiles=load_profiles(canonical=research),
                        rail_by_base=rail_by_base)


def render_d004_section(audit):
    s, c = audit["scope"], audit["counts"]
    lines = [
        "## D-004 — auditoria descritiva (recorte ainda não confirmado)",
        "",
        "A decisão oficial permanece sem lista fechada de finalistas no snapshot. "
        "Não há ranking, prioridade por cidade ou alteração da decisão. "
        "A união abaixo é um recorte documental, não uma seleção.",
        "",
        f"- Candidatas transcritas e revisadas do snapshot {s['named_candidates_reference_date']} (decisão no snapshot {s['snapshot_date']}: {s['decision_status']}): "
        + (", ".join(s["named_candidates"]) or "nenhuma candidata identificada") + ".",
        f"- Estudo de cinco bases ({s['five_base_study_date']}): "
        + ", ".join(s["five_base_study_ids"]) + ".",
        f"- Triagem histórica ({s['historical_shortlist_date']}): "
        + ", ".join(s["historical_shortlist_ids"]) + ". Não é o recorte D-004.",
        f"- Recorte prioritário de pesquisa autorizado em {s['research_scope_approved_at']}: "
        + ", ".join(s["approved_research_base_ids"]) + ". Não é decisão oficial de base.",
        "- Confirmar a decisão final D-004 com o responsável; nenhuma prioridade por cidade é atribuída.",
        "",
        f"Denominador descritivo: {c['bases']} bases únicas; a triagem histórica não amplia o denominador.",
        "",
        "| Evidência | Bases com registro | Denominador |",
        "|---|---:|---:|",
    ]
    for label, key in (
        ("Amostra histórica de moradia", "with_historical_housing"),
        ("Três cotações verificadas para 2027", "with_three_verified_quotes"),
        ("Restaurante para dois (referência histórica)", "with_restaurant"),
        ("Passe urbano nominal (referência histórica)", "with_urban_pass"),
        ("Cesta local completa comparável", "with_local_basket"),
        ("Normais climáticas de setembro a novembro", "with_climate"),
        ("Coworking pesquisado", "with_coworking"),
        ("Internet residencial confirmada para 2027", "with_residential_internet"),
    ):
        lines.append(f"| {label} | {c[key]} | {c['bases']} |")
    lines.extend([
        "", "### Evidências por base — sem pontuação", "",
        "| Base | Anúncios históricos | Cotações 2027 | Restaurante EUR/2 pessoas | Passe EUR/pessoa/mês | Clima | Coworking (2026) | Idas documentadas/não locais |",
        "|---|---:|---:|---:|---:|---|---|---:|",
    ])
    def fmt(value):
        return "Desconhecido" if value is None else format(value, "g")
    for r in audit["rows"]:
        h, d, w, rail = r["housing"], r["daily_life"], r["remote_work"], r["rail"]
        climate = "Documentado" if (d["climate"] or {}).get("months_9_10_11") is not None else "Desconhecido"
        state = {"compatible_2026": "Compatível na referência",
                 "incompatible_2026": "Horário insuficiente",
                 "indeterminate": "Indeterminado"}[w["compatibility_2026"]]
        lines.append(f"| {r['id']} | {h['summary']['count']} | "
                     f"{h['overview']['available_for_56_to_60_nights_2027']} | "
                     f"{fmt(d['restaurant_eur_two'])} | "
                     f"{fmt((d['urban_pass'] or {}).get('fare_eur_month_person'))} | "
                     f"{climate} | {state} | {rail['timed']}/{rail['eligible']} |")
    lines.extend(["", "### Lacunas por base — tipos de pesquisa, não prioridades oficiais", "",
                  "| Base | Necessário para comparar a escolha | Complementar | Suficiente apenas para contexto |",
                  "|---|---|---|---|"])
    for r in audit["rows"]:
        gaps = r["research_gaps"]
        parts = ["; ".join(gaps[k]) or "Nenhuma lacuna neste recorte"
                 for k in ("decision_blockers", "complementary", "sufficient_for_context_only")]
        lines.append(f"| {r['id']} | " + " | ".join(parts) + " |")
    lines.extend([
        "", "### Lacunas e condições para pesquisas seguintes", "",
        "- Moradia: comparar três unidades privativas para dois adultos, mesmas datas e 56–60 noites, "
        "preço total, taxas, caução separada, contrato, internet e estação. Anúncios EUR/mês de 2026 "
        "não são cotações; as amostras de mercado e pacotes podem repetir anúncios e não são somadas.",
        "- Vida cotidiana: pesquisar uma cesta local homogênea, lavanderia e condições dos passes; "
        "a cesta compartilhada do orçamento não é evidência de cidade. Restaurante e clima são contexto histórico.",
        "- Trabalho remoto: validar acesso no plano contratado e no expediente real, internet no imóvel e "
        "modalidades/taxas. Horário publicado não confirma acesso em 2027; sem inferência de fuso.",
        "- Logística: reutilizar os pares DATA24A; mínimos de ida não demonstram retorno ou porta a porta. "
        "O recorte de destinos relevante à decisão ainda precisa ser confirmado.",
        "- Evidência suficiente apenas para contexto: normais climáticas documentadas e observações históricas "
        "com fonte e unidade; nenhuma delas fecha os requisitos de 2027.",
        "", "O JSON completo gerado localmente pelo comando de reprodução (não versionado) "
        "contém os registros detalhados em d004. O anexo histórico compacto versionado não contém d004. "
        "As fontes originais podem ser consultadas diretamente no repositório, sem executar código:",
        "", "- [Moradia: anúncios, requisitos e datas](../../data/base_city_research_expanded_2026_11.json)",
        "- [Pacotes: bairros, clima, internet e referências de coworking](../../data/city_research_packs_2026_11.json)",
        "- [Alimentação e coworking: fontes, preços, modalidades e horários](../../data/city_research_round2_2026.json)",
        "- [Mercado: amostras, passes urbanos e premissas compartilhadas](../../data/city_market_observations_2026.json)",
        "- [Perfis: evidências públicas e limitações](../../data/city_profiles_enriched.json)",
        "- [Estudo de cinco bases](../../data/five_base_comparison_evidence_2026_11.json)",
        "- [Snapshot da decisão](../../data/trip.json)",
        "", "Contagens zero indicam ausência de registros verificados, nunca custo zero ou indisponibilidade comprovada.",
    ])
    return lines
