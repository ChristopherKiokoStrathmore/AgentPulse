"use client";

import {useEffect,useMemo,useRef,useState} from "react";
import {Activity,AlertTriangle,ArrowRight,ArrowUpRight,CheckCircle2,ChevronLeft,ChevronRight,Compass,ExternalLink,LocateFixed,MapPinned,Maximize2,Navigation,Radio,ScanLine,ShieldAlert,Wallet,WalletCards,X} from "lucide-react";

const MONEY=n=>"KES "+Math.round(Number(n||0)).toLocaleString("en-KE");
const HOT_RED="#ff4763",HOT_AMBER="#ffbe65",HOT_GREEN="#30d8a5";
const mapTheme="https://tiles.openfreemap.org/styles/dark";

function detailFor(outlet){
 if(!outlet)return {title:"Select an outlet",description:"Select a point on the map to investigate its balances.",severity:"Watch",reasons:[]};
 const threshold=outlet.status==="Critical"?135000:205000;
 const cashGap=Math.max(0,threshold-Number(outlet.cash||0));
 const floatGap=Math.max(0,threshold-Number(outlet.float||0));
 const reasons=[];
 if(cashGap>0)reasons.push({type:"Physical cash",gap:cashGap,message:"Cash is below the "+outlet.status.toLowerCase()+" alert threshold. Investigate withdrawal capacity and replenishment."});
 if(floatGap>0)reasons.push({type:"Electronic float",gap:floatGap,message:"E-float is below the "+outlet.status.toLowerCase()+" alert threshold. Investigate deposit capacity and float top up."});
 const title=cashGap&&floatGap?"Cash and float reserves need review":cashGap?"Low cash reserve":floatGap?"Low electronic float reserve":"Monitor liquidity position";
 const description="These are modelled balance threshold alerts, not confirmed declined transactions.";
 return {title,description,severity:outlet.status||"Watch",reasons,threshold};
}
const streetUrl=o=>"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint="+encodeURIComponent(o.lat+","+o.lng);
const mapsUrl=o=>"https://www.google.com/maps/search/?api=1&query="+encodeURIComponent(o.lat+","+o.lng);

function mapPoint(outlet){
 // Artistic network projection using approximate demo coordinates, not street accurate imagery.
 const x=16+Math.max(0,Math.min(1,(outlet.lng-36.73)/0.29))*68;
 const y=13+Math.max(0,Math.min(1,(-outlet.lat-1.12)/0.30))*74;
 return {x,y};
}

export function HeroPulse({outlets=[],risks=[],onOpen}){
 const [activeIndex,setActiveIndex]=useState(0);
 const [paused,setPaused]=useState(false);
 const reduced=useRef(false);
 useEffect(()=>{
  reduced.current=typeof window!=="undefined"&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
 },[]);
 useEffect(()=>{
  if(paused||risks.length<2||reduced.current)return;
  const timer=setInterval(()=>setActiveIndex(i=>(i+1)%Math.min(risks.length,8)),3700);
  return ()=>clearInterval(timer);
 },[paused,risks.length]);
 const focus=risks[activeIndex%Math.max(risks.length,1)]||risks[0];
 const issue=detailFor(focus);
 const points=outlets.map(o=>({...o,...mapPoint(o)}));
 const alarmPoints=points.filter(o=>o.status!=="Healthy");
 const hub={x:46,y:54};
 const links=alarmPoints.map((o,i)=>({
  key:o.id,
  d:"M "+o.x+" "+o.y+" Q "+(o.x+hub.x)/2+" "+(o.y+hub.y)/2+" "+hub.x+" "+hub.y,
  delay:(i%7)*0.34
 }));
 return <div className="ap-livehero ap-enter" onMouseEnter={()=>setPaused(true)} onMouseLeave={()=>setPaused(false)}>
  <div className="ap-livehero-grid" aria-hidden="true"/>
  <div className="ap-livehero-shimmer" aria-hidden="true"/>
  <div className="ap-livehero-copy">
   <div className="ap-livehero-overline"><span className="ap-record-dot"/> NETWORK INTELLIGENCE <span className="ap-livehero-divider"/> 30 OUTLETS</div>
   <button className="ap-livehero-headline" onClick={()=>onOpen(focus)} aria-label={"Investigate "+risks.length+" flagged outlets"}>
    <span className="ap-livehero-big">{risks.length}</span>
    <span>outlets need a<br/>liquidity review <ArrowUpRight size={22}/></span>
   </button>
   <p>Find the constraint. Explore its location. Understand what needs attention before moving capital.</p>
   <div className="ap-livehero-actions">
    <button className="ap-livehero-primary" onClick={()=>onOpen(focus)}>Investigate risks <ArrowRight size={17}/></button>
    <span className="ap-livehero-subline"><ScanLine size={15}/> Interactive Nairobi network</span>
   </div>
  </div>
  <div className="ap-livehero-visual">
   <div className="ap-livehero-map-caption"><span className="ap-livehero-tally"><Radio size={12}/> RISK RADAR</span><span>NAIROBI / NETWORK</span></div>
   <svg className="ap-livehero-roads" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
    <defs><linearGradient id="risk-flow" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#7c2538" stopOpacity="0"/><stop offset=".5" stopColor="#ff4b67" stopOpacity=".9"/><stop offset="1" stopColor="#ffc375" stopOpacity=".1"/></linearGradient></defs>
    <path d="M0 18L19 25L33 15L53 27L73 12L100 20M-4 55L16 39L38 43L58 39L80 47L102 40M-4 80L22 71L43 81L69 70L104 88M13 -2L22 24L13 49L24 75L20 102M52 -2L58 25L48 45L62 65L57 103M87 -2L76 25L82 49L72 80L88 102" stroke="#354358" strokeOpacity=".63" strokeWidth=".35" fill="none"/>
    {links.map(l=><path key={l.key} d={l.d} stroke="url(#risk-flow)" strokeWidth=".65" strokeDasharray="3 6" fill="none" className="ap-livehero-flow" style={{animationDelay:l.delay+"s"}}/>)}
   </svg>
   <div className="ap-livehero-crosshair" aria-hidden="true"><span/><span/></div>
   {points.map(o=>{
    const highlight=focus?.id===o.id;
    const isRisk=o.status!=="Healthy";
    return <button type="button" key={o.id} title={o.name+" · "+o.status} aria-label={"View "+o.name+" risk on map"} onClick={()=>onOpen(o)} className={"ap-livehero-dot "+(isRisk?"is-risk":"is-safe")+(highlight?" is-active":"")} style={{left:o.x+"%",top:o.y+"%",zIndex:highlight?7:isRisk?5:2}}>
      <span/>
    </button>;
   })}
   <div className="ap-livehero-location-label" aria-hidden="true">NAIROBI <span>36.82° E</span></div>
   {focus&&<button className="ap-livehero-focuscard" onClick={()=>onOpen(focus)} aria-label={"Investigate "+focus.name}>
    <span className="ap-focuscard-icon"><AlertTriangle size={16}/></span>
    <span className="ap-focuscard-text"><b>{focus.name}</b><small>{issue.title}</small></span>
    <ChevronRight size={17}/>
   </button>}
   <div className="ap-livehero-map-footer"><span><i/> HEALTHY</span><span className="amber"><i/> WATCH</span><span className="red"><i/> CRITICAL</span><span className="ap-hero-artnote">SCHEMATIC LOCATIONS</span></div>
  </div>
 </div>;
}

export function IncidentExplorer({outlets=[],initialOutlet,onClose}){
 const risks=useMemo(()=>outlets.filter(o=>o.status!=="Healthy").sort((a,b)=>{
  const aPriority=a.status==="Critical"?0:1,bPriority=b.status==="Critical"?0:1;
  return aPriority-bPriority||Math.min(a.cash,a.float)-Math.min(b.cash,b.float);
 }),[outlets]);
 const [current,setCurrent]=useState(initialOutlet||risks[0]||outlets[0]||null);
 const [camera,setCamera]=useState("street");
 const [filter,setFilter]=useState("All");
 const [styleMode,setStyleMode]=useState("Dark");
 const [mapError,setMapError]=useState(false);
 const mapEl=useRef(null);
 const mapRef=useRef(null);
 const markersRef=useRef([]);
 const currentRef=useRef(current);
 const initialRef=useRef(current);
 const selectRef=useRef(setCurrent);
 selectRef.current=setCurrent;
 currentRef.current=current;
 const viewing=detailFor(current);
 const visible=risks.filter(o=>filter==="All"||o.status===filter);
 const currentIndex=risks.findIndex(o=>o.id===current?.id);
 const lat=Number(current?.lat),lng=Number(current?.lng);
 useEffect(()=>{
  const key=e=>{if(e.key==="Escape")onClose();};
  document.addEventListener("keydown",key);
  const original=document.body.style.overflow;
  document.body.style.overflow="hidden";
  return ()=>{document.removeEventListener("keydown",key);document.body.style.overflow=original;};
 },[onClose]);
 useEffect(()=>{
  let disposed=false;
  let mapInstance=null;
  (async()=>{
   try{
    const maplibregl=(await import("maplibre-gl")).default;
    if(disposed||!mapEl.current||!initialRef.current)return;
    const first=initialRef.current;
    mapInstance=new maplibregl.Map({
     container:mapEl.current,
     style:mapTheme,
     center:[Number(first.lng),Number(first.lat)],
     zoom:15.6,
     pitch:62,
     bearing:-19,
     antialias:true,
     attributionControl:false
    });
    mapRef.current=mapInstance;
    mapInstance.addControl(new maplibregl.NavigationControl({visualizePitch:true}),"top-right");
    mapInstance.addControl(new maplibregl.AttributionControl({compact:true}),"bottom-right");
    mapInstance.on("load",()=>{
     setMapError(false);
     if(disposed)return;
     // The basemap may not carry building height attribution everywhere.
     try{
      const layers=mapInstance.getStyle().layers||[];
      const buildingLayer=layers.find(x=>x["source-layer"]==="building"&&x.source);
      if(buildingLayer&&!mapInstance.getLayer("ap-buildings")){
       const firstSymbol=layers.find(x=>x.type==="symbol");
       mapInstance.addLayer({
        id:"ap-buildings",type:"fill-extrusion",
        source:buildingLayer.source,"source-layer":"building",
        minzoom:14,paint:{
         "fill-extrusion-color":"#263445",
         "fill-extrusion-height":["interpolate",["linear"],["zoom"],14,0,15,["coalesce",["get","render_height"],["get","height"],8]],
         "fill-extrusion-base":["coalesce",["get","render_min_height"],["get","min_height"],0],
         "fill-extrusion-opacity":0.56
        }
       },firstSymbol?.id);
      }
     }catch(e){/* Some basemap styles have no extrudable buildings. */}
    });
    const markers=outlets.map(o=>{
     const el=document.createElement("button");
     el.type="button";
     el.className="ap-incident-marker "+(o.status==="Critical"?"critical":o.status==="Watch"?"watch":"healthy");
     el.title=o.name+" • "+o.status;
     el.setAttribute("aria-label","Select "+o.name);
     el.addEventListener("click",()=>selectRef.current(o));
     const marker=new maplibregl.Marker({element:el,anchor:"center"}).setLngLat([Number(o.lng),Number(o.lat)]).addTo(mapInstance);
     return marker;
    });
    markersRef.current=markers;
    const onResize=()=>mapInstance?.resize();
    window.addEventListener("resize",onResize);
    mapInstance.__apResize=onResize;
    setTimeout(()=>{if(!disposed)mapInstance?.resize();},450);
   }catch(e){if(!disposed)setMapError(true);}
  })();
  return ()=>{
   disposed=true;
   if(mapInstance?.__apResize)window.removeEventListener("resize",mapInstance.__apResize);
   markersRef.current.forEach(x=>x.remove());
   markersRef.current=[];
   if(mapInstance)mapInstance.remove();
   mapRef.current=null;
  };
 },[outlets]);
 useEffect(()=>{
  if(!current||!mapRef.current)return;
  const index=outlets.findIndex(o=>o.id===current.id);
  markersRef.current.forEach((m,i)=>m.getElement().classList.toggle("selected",i===index));
  mapRef.current.flyTo({
   center:[Number(current.lng),Number(current.lat)],
   zoom:camera==="street"?16.2:11.3,
   pitch:camera==="street"?64:28,
   bearing:camera==="street"?-18:0,
   essential:true,duration:1000
  });
 },[current,camera,outlets]);
 const next=()=>{if(!risks.length)return;setCurrent(risks[(Math.max(0,currentIndex)+1)%risks.length]);};
 const prev=()=>{if(!risks.length)return;setCurrent(risks[(Math.max(0,currentIndex)+risks.length-1)%risks.length]);};
 return <div className="ap-incident-backdrop" role="dialog" aria-modal="true" aria-label="Liquidity incident command map">
  <div className="ap-incident-window">
   <div className="ap-incident-top">
    <div className="ap-incident-heading"><span className="ap-command-logo"><Activity size={19}/></span><div><b>LIQUIDITY COMMAND</b><small>Investigate flagged Nairobi outlets</small></div></div>
    <div className="ap-incident-actions">
     <span className="ap-incident-count"><span/> {risks.length} flagged / {outlets.length} outlets</span>
     <button className="ap-map-icon-btn" title="Close investigation" onClick={onClose} aria-label="Close investigation"><X size={20}/></button>
    </div>
   </div>
   <div className="ap-incident-body">
    <aside className="ap-incident-sidebar">
     <div className="ap-incident-sidebar-intro"><div className="ap-incident-superline">NETWORK ALERTS / OCT 2026</div><h2>Every risk.<br/><span>One map.</span></h2><p>Choose an outlet to fly into its neighborhood and investigate the liquidity signal.</p></div>
     <div className="ap-incident-filter">
      {["All","Critical","Watch"].map(v=><button key={v} type="button" onClick={()=>setFilter(v)} className={filter===v?"active":""}>{v}{v==="All"?" "+risks.length:" "+risks.filter(o=>o.status===v).length}</button>)}
     </div>
     <div className="ap-incident-list">
      {visible.map(o=>{
       const d=detailFor(o);
       return <button key={o.id} type="button" onClick={()=>setCurrent(o)} className={"ap-incident-list-item "+(current?.id===o.id?"selected":"")}>
        <span className={"ap-incident-list-flag "+(o.status==="Critical"?"red":"amber")}>{o.status==="Critical"?<ShieldAlert size={15}/>:<AlertTriangle size={15}/>}</span>
        <span className="ap-incident-list-content"><b>{o.name}</b><small>{d.title}</small><em>{o.area} · {o.status}</em></span>
        <ChevronRight size={16}/>
       </button>;
      })}
     </div>
     <p className="ap-incident-confidential"><ShieldAlert size={14}/> Approximate demo locations, not confirmed agent storefronts.</p>
    </aside>
    <div className="ap-incident-map">
     <div className="ap-incident-map-base" ref={mapEl}/>
     {mapError&&<div className="ap-incident-fallback"><MapPinned size={32}/><h3>Map tiles unavailable</h3><p>Use the external maps link to inspect this approximate location.</p>{current&&<a target="_blank" rel="noopener noreferrer" href={mapsUrl(current)}>Open location map <ExternalLink size={15}/></a>}</div>}
     <div className="ap-incident-map-top"><span className="ap-incident-map-tag"><span/> 3D STREET MAP</span><div className="ap-incident-map-switch">{["street","network"].map(v=><button type="button" key={v} onClick={()=>setCamera(v)} className={camera===v?"active":""}>{v==="street"?"Street level":"Network"}</button>)}</div></div>
     <div className="ap-incident-crosshair"><LocateFixed size={21}/></div>
     <div className="ap-incident-map-bottom"><span><i className="critical"/> Critical</span><span><i className="watch"/> Watch</span><span><i className="healthy"/> Healthy</span><span className="ap-map-attribution">© OpenStreetMap contributors / OpenFreeMap</span></div>
    </div>
    <aside className="ap-incident-inspection">
     {current&&<>
      <div className="ap-inspection-photo"><div className="ap-inspection-signal"><Radio size={15}/> OUTLET SIGNAL</div><MapPinned size={46}/><span>LOCATION OVERVIEW</span></div>
      <div className="ap-inspection-content">
       <div className="ap-inspection-title"><div><span className="ap-incident-superline">INVESTIGATION / {current.id}</span><h2>{current.name}</h2><p>{current.area} · Nairobi</p></div><span className={"ap-inspection-badge "+current.status.toLowerCase()}>{current.status}</span></div>
       <div className="ap-inspection-issue"><div className="ap-inspection-issue-head"><AlertTriangle size={16}/> WHY IT WAS FLAGGED</div><h3>{viewing.title}</h3><p>{viewing.description}</p></div>
       <div className="ap-inspection-balances"><div><span><Wallet size={14}/> Cash reserve</span><strong>{MONEY(current.cash)}</strong></div><div><span><WalletCards size={14}/> Electronic float</span><strong>{MONEY(current.float)}</strong></div></div>
       {viewing.reasons.map(r=><div className="ap-inspection-reason" key={r.type}><div><b>{r.type}</b><strong>Below threshold by {MONEY(r.gap)}</strong></div><p>{r.message}</p></div>)}
       <div className="ap-inspection-actions"><a href={streetUrl(current)} target="_blank" rel="noopener noreferrer" className="ap-inspection-street"><Navigation size={17}/> Open Google Street View <ExternalLink size={14}/></a><a href={mapsUrl(current)} target="_blank" rel="noopener noreferrer" className="ap-inspection-maplink"><MapPinned size={15}/> Open Google Maps</a></div>
       <p className="ap-incident-caveat">Street View opens Google Maps externally. Nearby imagery may be unavailable or not show the outlet. An exact storefront requires verified coordinates and consent.</p>
      </div>
     </>}
     <div className="ap-inspection-footer"><button onClick={prev} aria-label="Previous flagged outlet"><ChevronLeft size={18}/></button><span>{currentIndex>=0?currentIndex+1:"—"} of {risks.length} flagged</span><button onClick={next} aria-label="Next flagged outlet"><ChevronRight size={18}/></button></div>
    </aside>
   </div>
  </div>
 </div>;
}
