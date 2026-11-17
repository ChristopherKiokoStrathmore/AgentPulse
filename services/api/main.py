"""AgentPulse prototype API: persisted synthetic finance data and optional public geo enrichment.
No Airtel Money integration, identity claims, or real money movement functionality.
"""
from __future__ import annotations
import json, math, os, random, urllib.request, urllib.parse
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint, select, func
from sqlalchemy.orm import declarative_base, Session

URL=os.getenv("DATABASE_URL", "sqlite:///./agentpulse.db")
if URL.startswith("postgres://"): URL=URL.replace("postgres://","postgresql+psycopg://",1)
elif URL.startswith("postgresql://"): URL=URL.replace("postgresql://","postgresql+psycopg://",1)
engine=create_engine(URL,pool_pre_ping=True,connect_args={"check_same_thread":False} if URL.startswith("sqlite") else {})
Base=declarative_base()
FACTORS=["population","commercial","accessibility","competition","economics","coverage"]
DEFAULT=dict(zip(FACTORS,[25,20,15,15,15,10]))
OUTLET_POINTS=[
("Kimathi Street","CBD",-1.2841,36.822),("Sarit Centre","Westlands",-1.262,36.8011),
("Eastleigh 1st Avenue","Eastleigh",-1.2808,36.8482),("Githurai 44","Githurai",-1.2032,36.912),
("Ruiru Town","Ruiru",-1.148,36.961),("Roysambu","Roysambu",-1.2186,36.884),
("Kasarani Seasons","Kasarani",-1.2258,36.8998),("Kahawa West","Kahawa West",-1.18,36.9067),
("Umoja Innercore","Umoja",-1.2806,36.892),("Kayole Junction","Kayole",-1.2854,36.922),
("Donholm","Donholm",-1.2938,36.8865),("Buruburu","Buruburu",-1.282,36.879),
("South B","South B",-1.3117,36.835),("South C","South C",-1.3169,36.8284),
("Langata","Langata",-1.332,36.778),("Kibera Olympic","Kibera",-1.312,36.787),
("Ngong Road","Ngong Road",-1.3006,36.764),("Kawangware","Kawangware",-1.2787,36.7491),
("Kilimani Yaya","Kilimani",-1.2925,36.7832),("Lavington","Lavington",-1.2761,36.7702),
("Parklands","Parklands",-1.2551,36.8143),("Pangani Stage","Pangani",-1.2657,36.8394),
("Ngara Market","Ngara",-1.268,36.8254),("Kariobangi North","Kariobangi",-1.254,36.8825),
("Dandora","Dandora",-1.2539,36.9021),("Pipeline","Embakasi",-1.318,36.914),
("Utawala","Utawala",-1.2895,36.9678),("Ruaka Town","Ruaka",-1.2088,36.7786),
("Ridgeways","Kiambu Road",-1.2266,36.8255),("Mwiki Shopping","Mwiki",-1.2003,36.9204)]
CANDIDATE_POINTS=[
("Gikomba Market","Gikomba",-1.2836,36.8405,27000),
("Zimmerman Stage","Zimmerman",-1.2027,36.878,23000),
("Kangemi Shopping","Kangemi",-1.268,36.741,22000),
("Mlolongo Interchange","Mlolongo",-1.393,36.946,25000),
("Kikuyu Town","Kikuyu",-1.246,36.664,20000),
("Juja Farm Junction","Juja",-1.1026,37.0146,18000),
("Ongata Rongai Stage","Rongai",-1.396,36.757,30000),
("Syokimau Station","Syokimau",-1.3614,36.9167,34000)]

class Outlet(Base):
    __tablename__="outlets"
    id=Column(String,primary_key=True)
    name=Column(String,nullable=False)
    area=Column(String,nullable=False)
    lat=Column(Float,nullable=False)
    lng=Column(Float,nullable=False)
    cash=Column(Numeric(16,2),nullable=False)
    efloat=Column(Numeric(16,2),nullable=False)
    monthly_tx=Column(Integer,nullable=False)
    commission=Column(Numeric(16,2),nullable=False)
    status=Column(String,nullable=False)
    provenance=Column(String,nullable=False,default="synthetic")
class Transaction(Base):
    __tablename__="transactions"
    id=Column(String,primary_key=True)
    outlet_id=Column(String,ForeignKey("outlets.id"),nullable=False,index=True)
    event_at=Column(DateTime(timezone=True),nullable=False,index=True)
    kind=Column(String,nullable=False)
    amount=Column(Numeric(16,2),nullable=False)
    commission=Column(Numeric(16,2),nullable=False)
    status=Column(String,nullable=False)
    provenance=Column(String,nullable=False,default="synthetic")
class Ledger(Base):
    __tablename__="ledger_entries"
    id=Column(Integer,primary_key=True,autoincrement=True)
    transaction_id=Column(String,ForeignKey("transactions.id"),nullable=False,index=True)
    outlet_id=Column(String,ForeignKey("outlets.id"),nullable=False)
    account=Column(String,nullable=False)
    delta=Column(Numeric(16,2),nullable=False)
class Month(Base):
    __tablename__="monthly_summaries"
    id=Column(Integer,primary_key=True)
    outlet_id=Column(String,ForeignKey("outlets.id"),nullable=False)
    month=Column(String,nullable=False)
    tx_count=Column(Integer,nullable=False)
    volume=Column(Numeric(18,2),nullable=False)
    __table_args__=(UniqueConstraint("outlet_id","month"),)
class Candidate(Base):
    __tablename__="candidate_sites"
    id=Column(String,primary_key=True)
    name=Column(String,nullable=False)
    area=Column(String,nullable=False)
    lat=Column(Float,nullable=False)
    lng=Column(Float,nullable=False)
    rent=Column(Integer,nullable=False)
    startup=Column(Integer,nullable=False)
    features_json=Column(String,nullable=False)
    population_500m=Column(Float,nullable=True)
    population_source=Column(String,nullable=True)
    provenance=Column(String,nullable=False,default="synthetic")
class WeightProfile(Base):
    __tablename__="weight_profiles"
    id=Column(String,primary_key=True)
    label=Column(String,nullable=False)
    weights_json=Column(String,nullable=False)
    created_at=Column(DateTime(timezone=True),nullable=False)
class ProviderCache(Base):
    __tablename__="provider_cache"
    id=Column(String,primary_key=True)
    checked_at=Column(DateTime(timezone=True),nullable=False)
    status=Column(String,nullable=False)
    payload_json=Column(String,nullable=False)

def seed():
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        if db.scalar(select(func.count()).select_from(Outlet))>0: return
        rng=random.Random(20261117)
        pending_ledger=[]
        pending_transactions=[]
        pending_months=[]
        for i,(name,area,lat,lng) in enumerate(OUTLET_POINTS):
            oid=f"AP-{i+1:03d}"
            cash=Decimal(rng.randrange(190000,390000,100))
            efloat=Decimal(rng.randrange(170000,370000,100))
            completed=0
            fee_sum=Decimal(0)
            # Posted events are internally balanced and cannot overdraw either balance.
            for j in range(60):
                kind="Deposit" if rng.random()<0.52 else "Withdrawal"
                amount=Decimal(rng.randrange(500,14500,100))
                if kind=="Deposit" and amount>efloat or kind=="Withdrawal" and amount>cash: continue
                change_cash=amount if kind=="Deposit" else -amount
                change_float=-change_cash
                cash+=change_cash; efloat+=change_float
                tid=f"SIM-{i+1:03d}-{j+1:03d}"
                fee=(amount*Decimal("0.006")).quantize(Decimal("1"))
                fee_sum+=fee
                completed+=1
                date=datetime(2026,10,31,18,tzinfo=timezone.utc)-timedelta(hours=j*11+i)
                pending_transactions.append(Transaction(id=tid,outlet_id=oid,event_at=date,kind=kind,
                    amount=amount,commission=fee,status="Completed"))
                pending_ledger.append(Ledger(transaction_id=tid,outlet_id=oid,account="CASH",delta=change_cash))
                pending_ledger.append(Ledger(transaction_id=tid,outlet_id=oid,account="EFLOAT",delta=change_float))
            state="Critical" if min(cash,efloat)<135000 else "Watch" if min(cash,efloat)<205000 else "Healthy"
            monthly_tx=rng.randint(1900,5100)
            db.add(Outlet(id=oid,name=name,area=area,lat=lat,lng=lng,cash=cash,efloat=efloat,
                          monthly_tx=monthly_tx,commission=fee_sum,status=state))
            for k in range(36):
                year=2023+(k+10)//12
                month=(k+10)%12+1
                seasonal=1.17 if month==12 else 1.08 if month in (1,8) else 1
                count=int((1200+k*51+i*38)*seasonal*rng.uniform(.85,1.15))
                pending_months.append(Month(outlet_id=oid,month=f"{year}-{month:02d}",tx_count=count,
                            volume=Decimal(count*rng.randint(1300,2400))))
        for i,(name,area,lat,lng,rent) in enumerate(CANDIDATE_POINTS):
            r=random.Random(9000+i)
            feats={key:r.randint(48,92) for key in FACTORS}
            db.add(Candidate(id=f"SITE-{i+1}",name=name,area=area,lat=lat,lng=lng,rent=rent,
                             startup=225000+i*17000,features_json=json.dumps(feats)))
        db.flush()  # First persist all parent outlets and candidates.
        db.add_all(pending_transactions)
        db.add_all(pending_months)
        db.flush()  # Then persist transactions and summaries before ledger rows.
        db.add_all(pending_ledger)
        db.commit()

@asynccontextmanager
async def lifespan(app:FastAPI):
    seed()
    yield

app=FastAPI(title="AgentPulse Financial Operations API",version="0.2.0",lifespan=lifespan)
origins=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:3000,https://agentpulse-nairobi-mvp.vercel.app").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["*"])

def serialize_outlet(o):
    return {"id":o.id,"name":o.name,"area":o.area,"lat":o.lat,"lng":o.lng,
      "cash_kes":float(o.cash),"efloat_kes":float(o.efloat),"monthly_transactions":o.monthly_tx,
      "commission_kes":float(o.commission),"status":o.status,"source":o.provenance}
def serialize_site(c):
    return {"id":c.id,"name":c.name,"area":c.area,"lat":c.lat,"lng":c.lng,
      "monthly_rent_kes":c.rent,"startup_kes":c.startup,"factors":json.loads(c.features_json),
      "population_500m":c.population_500m,"population_source":c.population_source,
      "source":"mixed" if c.population_500m is not None else "synthetic"}

@app.get("/health")
def health():
    with Session(engine) as db: count=db.scalar(select(func.count()).select_from(Outlet))
    return {"status":"ok","database":"connected","outlets":count,"operational_data":"synthetic"}
@app.get("/v1/overview")
def overview():
    with Session(engine) as db:
        outlets=db.scalars(select(Outlet)).all()
        return {"period":"2026-10","outlets":len(outlets),
            "cash_kes":sum(float(x.cash) for x in outlets),
            "efloat_kes":sum(float(x.efloat) for x in outlets),
            "commission_kes":sum(float(x.commission) for x in outlets),
            "monthly_transactions":sum(x.monthly_tx for x in outlets),
            "critical_outlets":sum(x.status=="Critical" for x in outlets),
            "source":"synthetic"}
@app.get("/v1/outlets")
def outlets():
    with Session(engine) as db:
        return {"source":"synthetic","data":[serialize_outlet(x) for x in db.scalars(select(Outlet).order_by(Outlet.id))]}
@app.get("/v1/transactions")
def transactions(limit:int=Query(200,ge=1,le=500),outlet_id:str|None=None):
    with Session(engine) as db:
        q=select(Transaction).order_by(Transaction.event_at.desc()).limit(limit)
        if outlet_id:q=q.where(Transaction.outlet_id==outlet_id)
        rows=db.scalars(q).all()
        return {"source":"synthetic","data":[{"id":x.id,"outlet_id":x.outlet_id,
            "timestamp":x.event_at.isoformat(),"type":x.kind,"amount_kes":float(x.amount),
            "commission_kes":float(x.commission),"status":x.status} for x in rows]}
@app.get("/v1/monthly")
def monthly():
    with Session(engine) as db:
        results=db.execute(select(Month.month,func.sum(Month.volume),func.sum(Month.tx_count)).group_by(Month.month).order_by(Month.month)).all()
        return {"source":"synthetic","data":[{"period":a,"value":float(b),"count":int(c)} for a,b,c in results]}
@app.get("/v1/ledger/check")
def ledger_check():
    with Session(engine) as db:
        rows=db.execute(select(Ledger.transaction_id,func.sum(Ledger.delta)).group_by(Ledger.transaction_id)).all()
        bad=[tid for tid,total in rows if total!=0]
        return {"checked":len(rows),"balanced":not bad,"unbalanced_ids":bad}

@app.get("/v1/geo/candidates")
def candidates():
    with Session(engine) as db:return {"data":[serialize_site(c) for c in db.scalars(select(Candidate).order_by(Candidate.id))]}

class ScoreRequest(BaseModel):
    weights:dict[str,float]
    max_monthly_rent_kes:int=Field(45000,ge=0,le=1000000)

def check_weights(weights):
    if not weights or any(k not in FACTORS or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for k,v in weights.items()):
        raise HTTPException(422,"Invalid scoring dimensions or weights")
    total=sum(weights.values())
    if total<=0:raise HTTPException(422,"At least one weight must be positive")
    return {k:weights.get(k,0)/total for k in FACTORS}

@app.post("/v1/geo/scores/preview")
def preview(req:ScoreRequest):
    normalized=check_weights(req.weights)
    with Session(engine) as db:
        candidates=[serialize_site(c) for c in db.scalars(select(Candidate))]
    scored=[]
    for c in candidates:
        if c["monthly_rent_kes"]>req.max_monthly_rent_kes:continue
        contrib={k:round(normalized[k]*c["factors"][k],3) for k in FACTORS}
        scored.append({**c,"score":round(sum(contrib.values()),2),"contributions":contrib})
    scored.sort(key=lambda s:s["score"],reverse=True)
    return {"weights":normalized,"data":scored,"score_source":"mixed_estimate",
      "limitations":"Only population may be externally sourced; other factors are simulated."}

class ProfileRequest(BaseModel):
    label:str=Field("Custom strategy",max_length=80)
    weights:dict[str,float]
@app.get("/v1/geo/weight-profiles")
def profiles():
    with Session(engine) as db:
        rows=db.scalars(select(WeightProfile).order_by(WeightProfile.created_at.desc()).limit(40)).all()
        return {"data":[{"id":p.id,"label":p.label,"weights":json.loads(p.weights_json),"created_at":p.created_at.isoformat()} for p in rows]}
@app.post("/v1/geo/weight-profiles")
def save_profile(req:ProfileRequest):
    normalized=check_weights(req.weights)
    profile=WeightProfile(id=str(uuid4()),label=req.label,weights_json=json.dumps(normalized),
                          created_at=datetime.now(timezone.utc))
    with Session(engine) as db: db.add(profile);db.commit()
    return {"id":profile.id,"label":profile.label,"weights":normalized,"persisted":True}

def http_json(url,body=None,timeout=8):
    headers={"User-Agent":"AgentPulseDemo/0.2 (educational nonprofit prototype)","Accept":"application/json"}
    if body is not None: headers["Content-Type"]="application/json"
    request=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,
                                   headers=headers,method="POST" if body is not None else "GET")
    with urllib.request.urlopen(request,timeout=timeout) as response:return json.load(response)

@app.get("/v1/geo/public-context")
def public_context(refresh:bool=False):
    """Cached public data. No claim that simulated financial scores are measured data."""
    if refresh: raise HTTPException(403,"External refresh is controlled by cache expiry")
    with Session(engine) as db:
        cached=db.get(ProviderCache,"public_context")
        if cached and not refresh and (datetime.now(timezone.utc)-cached.checked_at.replace(tzinfo=timezone.utc)).total_seconds()<86400:
            return json.loads(cached.payload_json)
        candidates=db.scalars(select(Candidate).order_by(Candidate.id)).all()
        points=[{"id":c.id,"lat":c.lat,"lon":c.lng} for c in candidates]
        data={"worldpop":{"status":"unavailable"},"open_meteo":{"status":"unavailable"},
              "osm":{"status":"map_baselayer_only","note":"No measured traffic data"}}
        try:
            wp=http_json("https://api.worldpop.org/v3/catchment",
                  {"points":points,"radii_km":[0.5,1.0],"year":2026},timeout=12)
            lookup={p["id"]:p for p in wp.get("points",[])}
            vals=[]
            for c in candidates:
                rec=lookup.get(c.id)
                if rec and rec.get("rings"):
                    value=float(rec["rings"][0]["cumulative"])
                    c.population_500m=value
                    c.population_source="WorldPop Global2 2026"
                    vals.append(value)
            if vals:
                floor,ceil=min(vals),max(vals)
                for c in candidates:
                    if c.population_500m is not None:
                        f=json.loads(c.features_json)
                        f["population"]=int(50+45*(c.population_500m-floor)/max(ceil-floor,1))
                        c.features_json=json.dumps(f)
                data["worldpop"]={"status":"live_cached","year":2026,"candidates":len(vals),
                   "attribution":"WorldPop Global2, CC BY 4.0"}
        except Exception as exc:data["worldpop"]={"status":"unavailable","error_type":type(exc).__name__}
        try:
            q=urllib.parse.urlencode({"latitude":-1.2864,"longitude":36.8219,
                                      "start_date":"2026-10-01","end_date":"2026-10-31",
                                      "daily":"precipitation_sum","timezone":"Africa/Nairobi"})
            response=http_json("https://archive-api.open-meteo.com/v1/archive?"+q,timeout=12)
            vals=[float(x) for x in response.get("daily",{}).get("precipitation_sum",[]) if x is not None]
            if vals:
                data["open_meteo"]={"status":"live_cached","period":"2026-10",
                 "rainfall_mm":round(sum(vals),1),"attribution":"Open-Meteo CC BY 4.0"}
        except Exception as exc:data["open_meteo"]={"status":"unavailable","error_type":type(exc).__name__}
        data["updated_at"]=datetime.now(timezone.utc).isoformat()
        if cached:
            cached.status="cached";cached.payload_json=json.dumps(data)
            cached.checked_at=datetime.now(timezone.utc)
        else:db.add(ProviderCache(id="public_context",checked_at=datetime.now(timezone.utc),status="cached",payload_json=json.dumps(data)))
        db.commit()
        return data

@app.get("/v1/data-sources")
def sources():
    return {"operational":{"type":"synthetic","period":"Nov 2023 to Oct 2026",
       "claim":"Not Airtel Money records"},"population":{"provider":"WorldPop","live_cache_endpoint":"/v1/geo/public-context"},
       "weather":{"provider":"Open-Meteo","live_cache_endpoint":"/v1/geo/public-context"},
       "roads":{"provider":"OpenStreetMap","status":"public map tiles only; no live traffic counts"}}


def distance_m(a_lat,a_lon,b_lat,b_lon):
    """Haversine distance in meters between geographic coordinates."""
    earth=6371008.8
    p1,p2=math.radians(a_lat),math.radians(b_lat)
    dp=math.radians(b_lat-a_lat)
    dl=math.radians(b_lon-a_lon)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*earth*math.asin(min(1,math.sqrt(x)))

@app.get("/v1/geo/osm-context")
def osm_context():
    """Cache public OSM POI proxies for commercial activity and access.
    OSM is not actual footfall, congestion or Airtel competitor registration data.
    """
    with Session(engine) as db:
        cache=db.get(ProviderCache,"osm_pois")
        if cache:
            checked=cache.checked_at.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc)-checked).total_seconds()<86400:
                return json.loads(cache.payload_json)
        bounds="(-1.42,36.62,-1.08,37.04)"
        query=('[out:json][timeout:20];('
               'node["amenity"~"^(bank|atm|marketplace|bus_station)$"]'+bounds+';'
               'node["shop"~"^(supermarket|convenience|mall)$"]'+bounds+';'
               ');out body;')
        result={"status":"unavailable","source":"OpenStreetMap Overpass",
                "limitations":"POI count is a coverage proxy, not measured traffic or confirmed Airtel competition."}
        try:
            req=urllib.request.Request(
                "https://overpass-api.de/api/interpreter",
                data=urllib.parse.urlencode({"data":query}).encode(),
                headers={"Content-Type":"application/x-www-form-urlencoded",
                         "User-Agent":"AgentPulseDemo/0.2 (research demo)"},
                method="POST")
            with urllib.request.urlopen(req,timeout=13) as response:
                osm=json.load(response)
            nodes=[n for n in osm.get("elements",[]) if "lat" in n and "lon" in n]
            candidates=db.scalars(select(Candidate)).all()
            counts={}
            for c in candidates:
                local=[n for n in nodes if distance_m(c.lat,c.lng,n["lat"],n["lon"])<=650]
                commerce=sum(n.get("tags",{}).get("shop") is not None or
                             n.get("tags",{}).get("amenity")=="marketplace" for n in local)
                transport=sum(n.get("tags",{}).get("amenity")=="bus_station" for n in local)
                finance=sum(n.get("tags",{}).get("amenity") in ("bank","atm") for n in local)
                f=json.loads(c.features_json)
                f["commercial"]=min(95,50+min(commerce,20)*2)
                f["accessibility"]=min(95,50+min(transport,9)*5)
                c.features_json=json.dumps(f)
                counts[c.id]={"commercial_pois":commerce,"transport_pois":transport,
                              "financial_service_pois":finance}
            result={"status":"live_cached","source":"OpenStreetMap Overpass",
                    "pois_count":len(nodes),"candidate_counts":counts,
                    "attribution":"© OpenStreetMap contributors, ODbL",
                    "limitations":"POIs are incomplete and do not measure traffic or identify mobile money franchise competition."}
        except Exception as exc:
            result["error_type"]=type(exc).__name__
        result["updated_at"]=datetime.now(timezone.utc).isoformat()
        if cache:
            cache.payload_json=json.dumps(result)
            cache.checked_at=datetime.now(timezone.utc)
            cache.status=result["status"]
        else:
            db.add(ProviderCache(id="osm_pois",checked_at=datetime.now(timezone.utc),
                                 status=result["status"],payload_json=json.dumps(result)))
        db.commit()
        return result
