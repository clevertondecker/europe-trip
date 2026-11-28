"""UX3.8: bounded, exploratory travel quotes; not payments, reservations or commitments.

Money is serialized as Decimal strings. Quotes never mutate the TripPlan,
published evidence, budget spreadsheet or financial baseline.
"""
from __future__ import annotations
import json
from copy import deepcopy
from datetime import date,datetime,timezone
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from uuid import UUID,uuid4


CATEGORIES=("housing","flight","intercity_train","local_transport","outing","ticket")
UNITS=("stay","person_oneway","person_roundtrip","couple_roundtrip",
       "person","couple","night","month","visit")
CURRENCIES=("BRL","EUR","CHF")
LIMIT=60
MAX_BYTES=350_000


def _money(value:str)->Decimal:
    if not isinstance(value,str) or not value or len(value)>24:
        raise ValueError("Valor deve ser decimal em texto")
    try:amount=Decimal(value)
    except (InvalidOperation,ValueError) as exc:
        raise ValueError("Valor monetário inválido") from exc
    if not amount.is_finite() or amount<=0 or amount>Decimal("10000000"):
        raise ValueError("Valor fora dos limites")
    return amount


def _day(value):
    if value is None:return None
    if not isinstance(value,str):raise ValueError("Data inválida")
    return date.fromisoformat(value)


def validate_quote(quote:dict)->dict:
    required={"id","plan_id","name","category","city_id","amount","currency","unit",
              "quantity","travelers","start_date","end_date","source_url",
              "researched_at","notes","favorite"}
    if not isinstance(quote,dict) or set(quote)!=required:
        raise ValueError("Formato da cotação inválido")
    try:
        ident=UUID(quote["id"])
        if str(ident)!=quote["id"]:raise ValueError()
    except (ValueError,AttributeError,TypeError) as exc:
        raise ValueError("Identificador de cotação inválido") from exc
    pid=quote["plan_id"]
    if not isinstance(pid,str) or not pid.startswith("trip-") or len(pid)>100:
        raise ValueError("Plano associado inválido")
    if not isinstance(quote["name"],str) or not 1<=len(quote["name"].strip())<=90:
        raise ValueError("Descrição da cotação inválida")
    if quote["category"] not in CATEGORIES or quote["unit"] not in UNITS or quote["currency"] not in CURRENCIES:
        raise ValueError("Categoria, unidade ou moeda inválida")
    city=quote["city_id"]
    if city is not None and (not isinstance(city,str) or len(city)>80 or
                            not city.replace("_","").replace("-","").isalnum()):
        raise ValueError("Cidade inválida")
    _money(quote["amount"])
    if type(quote["quantity"]) is not int or not 1<=quote["quantity"]<=120:
        raise ValueError("Quantidade inválida")
    if type(quote["travelers"]) is not int or not 1<=quote["travelers"]<=10:
        raise ValueError("Viajantes inválidos")
    start,end=_day(quote["start_date"]),_day(quote["end_date"])
    if (start is None)!=(end is None) or (start and end<=start):
        raise ValueError("Período inválido; fim deve ser posterior ao início")
    if (quote["category"]=="housing" and quote["unit"]=="stay" and start is None):
        raise ValueError("Estadia completa exige período")
    link=quote["source_url"]
    if link is not None and (not isinstance(link,str) or len(link)>400 or
                             not link.startswith("https://")):
        raise ValueError("Fonte inválida")
    researched=quote["researched_at"]
    if not isinstance(researched,str) or date.fromisoformat(researched)>date.today():
        raise ValueError("Data de pesquisa inválida")
    if not isinstance(quote["notes"],str) or len(quote["notes"])>700:
        raise ValueError("Observações inválidas")
    if type(quote["favorite"]) is not bool:
        raise ValueError("Favorito inválido")
    return deepcopy(quote)


def new_quote(plan_id:str,name:str,category:str,amount:str,currency:str,unit:str,
              *,city_id:str|None=None,quantity:int=1,travelers:int=2,
              start_date:str|None=None,end_date:str|None=None,
              source_url:str|None=None,notes:str="",favorite:bool=False,
              researched_at:str|None=None)->dict:
    raw={"id":str(uuid4()),"plan_id":plan_id,"name":name,"category":category,
         "city_id":city_id,"amount":amount,"currency":currency,"unit":unit,
         "quantity":quantity,"travelers":travelers,"start_date":start_date,
         "end_date":end_date,"source_url":source_url,"researched_at":researched_at or date.today().isoformat(),
         "notes":notes,"favorite":favorite}
    return validate_quote(raw)


def empty_collection()->dict:
    return {"schema_version":1,"revision":0,"quotes":[]}


def validate_collection(data:dict)->dict:
    if not isinstance(data,dict) or set(data)!={"schema_version","revision","quotes"} or data["schema_version"]!=1:
        raise ValueError("Coleção de cotações incompatível")
    if type(data["revision"]) is not int or data["revision"]<0:
        raise ValueError("Revisão inválida")
    quotes=data["quotes"]
    if not isinstance(quotes,list) or len(quotes)>LIMIT:
        raise ValueError("Limite de cotações excedido")
    seen=set()
    for quote in quotes:
        valid=validate_quote(quote)
        if valid["id"] in seen:raise ValueError("Cotação duplicada")
        seen.add(valid["id"])
    return deepcopy(data)


def encode_collection(data:dict)->bytes:
    raw=json.dumps(validate_collection(data),ensure_ascii=False,sort_keys=True).encode("utf-8")
    if len(raw)>MAX_BYTES:raise ValueError("Coleção muito grande")
    return raw


def decode_collection(raw:bytes)->dict:
    if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_BYTES:
        raise ValueError("Arquivo de cotações inválido")
    try:return validate_collection(json.loads(raw.decode("utf-8")))
    except (UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError("JSON de cotações inválido") from exc


def upsert_quote(collection:dict,quote:dict)->dict:
    data=validate_collection(collection)
    quote=validate_quote(quote)
    idx=next((i for i,q in enumerate(data["quotes"]) if q["id"]==quote["id"]),None)
    if idx is None:
        if len(data["quotes"])>=LIMIT:raise ValueError("Limite atingido")
        data["quotes"].append(quote)
    else:
        if data["quotes"][idx]["plan_id"]!=quote["plan_id"]:
            raise ValueError("Não transferir cotação entre planos")
        data["quotes"][idx]=quote
    data["revision"]+=1
    return data


def remove_quote(collection:dict,quote_id:str)->dict:
    data=validate_collection(collection)
    remain=[q for q in data["quotes"] if q["id"]!=quote_id]
    if len(remain)==len(data["quotes"]):raise ValueError("Cotação ausente")
    data["quotes"]=remain
    data["revision"]+=1
    return data


def comparable_quotes(a:dict,b:dict)->bool:
    """Avoid pretending disparate prices refer to the same item or trip."""
    a,b=validate_quote(a),validate_quote(b)
    keys=("plan_id","category","city_id","currency","unit","quantity",
          "travelers","start_date","end_date")
    return all(a[k]==b[k] for k in keys)


def quote_difference(a:dict,b:dict)->Decimal|None:
    if not comparable_quotes(a,b):return None
    return (_money(b["amount"])-_money(a["amount"]))*a["quantity"]


def housing_budget_whatif(quote:dict,plan:dict,allowance_brl,*,fx_brl_per_unit:str|None=None)->dict:
    """ONLY complete France stay, in the official base, for two people.

    This is a replacement what-if (quote - existing France housing allowance),
    not a new expense. All non-comparable situations remain unknown.
    """
    q=validate_quote(quote)
    reason="Cotação não comparável à provisão completa de moradia"
    if (q["plan_id"]!=plan["plan_id"] or q["category"]!="housing"
            or q["city_id"]!=plan["base_city"] or q["unit"]!="stay"
            or q["quantity"]!=1 or q["travelers"]!=2):
        return {"delta_brl":None,"reason":reason}
    if q["start_date"] is None or q["end_date"] is None:
        return {"delta_brl":None,"reason":"Período desconhecido"}
    arrival=date.fromisoformat(plan["departure_date"])
    from datetime import timedelta
    france_start=arrival+timedelta(days=plan["italy_days"])
    france_end=arrival+timedelta(days=plan["total_days"])
    if (date.fromisoformat(q["start_date"])!=france_start or
            date.fromisoformat(q["end_date"])!=france_end):
        return {"delta_brl":None,"reason":"Datas da cotação não cobrem exatamente a estadia prevista"}
    if q["currency"]=="BRL":
        rate=Decimal("1")
    elif fx_brl_per_unit is None:
        return {"delta_brl":None,"reason":"Câmbio de simulação não informado"}
    else:
        rate=_money(fx_brl_per_unit)
    try:allowance=Decimal(str(allowance_brl))
    except (ValueError,InvalidOperation,TypeError) as exc:
        raise ValueError("Provisão inválida") from exc
    if not allowance.is_finite() or allowance<0:raise ValueError("Provisão inválida")
    actual=_money(q["amount"])*rate
    delta=(actual-allowance).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
    return {"delta_brl":str(delta),"reason":"Substituição hipotética da verba de moradia, não despesa adicional"}


def cloud_load(store)->tuple[dict,int|None]:
    result=store.load()
    if result is None:return empty_collection(),None
    raw,gen=result
    return decode_collection(raw),gen


def cloud_save(store,collection,generation:int|None)->int:
    return store.save(encode_collection(collection),generation)
