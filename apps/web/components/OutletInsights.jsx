"use client";

import {useEffect,useMemo,useRef,useState} from "react";
import {
 Area,AreaChart,Bar,BarChart,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis
} from "recharts";
import {
 Activity,ArrowDownRight,ArrowUpRight,BarChart3,CalendarRange,ChevronDown,Clock3,
 Download,ExternalLink,Info,MapPin,ReceiptText,RefreshCw,TrendingUp,Wallet,WalletCards,X
} from "lucide-react";

const KES=n=>"KES "+Math.round(Number(n||0)).toLocaleString("en-KE");
const NUM=n=>Math.round(Number(n||0)).toLocaleString("en-KE");
const SHORT=n=>Math.abs(Number(n||0))>=1e6?(n/1e6).toFixed(1)+"M":Math.abs(Number(n||0))>=1e3?(n/1e3).toFixed(1)+"K":NUM(n);
const MONTHS=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const labelMonth=m=>{const [year,month]=(m||"").split("-");return year&&month?MONTHS[Number(month)-1]+" '"+year.slice(2):m;};
const chartTooltip={
 contentStyle:{background:"#142130",border:"1px solid #41566b",borderRadius:10,color:"#fff",boxShadow:"0 14px 35px #01050ab3",fontSize:11},
 labelStyle:{color:"#f4f8ff",fontWeight:800},itemStyle:{color:"#fff",fontWeight:700}
};

const pctText=v=>v===null||v===undefined?"No comparison":(v>0?"+":"")+v.toFixed(1)+"%";
function Metric({label,value,sub,icon:Icon,color="teal"}){
 return <div className={"ap-in-metric "+color}>
  <span><Icon size={15}/>{label}</span>
  <strong>{value}</strong>
  <small>{sub}</small>
 </div>;
}

export default function OutletInsights({outlet,onClose,apiBase}){
 const cache=useRef({});
 const [data,setData]=useState(null);
 const [loading,setLoading]=useState(true);
 const [error,setError]=useState("");
 const [reload,setReload]=useState(0);
 const [tab,setTab]=useState("Overview");
 const [period,setPeriod]=useState("All 36 months");
 const [metric,setMetric]=useState("value");
 const [transactionsSearch,setTransactionsSearch]=useState("");

 useEffect(()=>{
  if(!outlet?.id)return;
  setTab("Overview");
  setPeriod("All 36 months");
  setMetric("value");
  setTransactionsSearch("");
 },[outlet?.id]);
 useEffect(()=>{
  if(!outlet?.id)return;
  if(cache.current[outlet.id]&&reload===0){
   setData(cache.current[outlet.id]);setLoading(false);setError("");return;
  }
  if(!apiBase){setError("The historical data API is not configured.");setLoading(false);setData(null);return;}
  const controller=new AbortController();
  setData(null);setLoading(true);setError("");
  fetch(apiBase+"/v1/outlets/"+encodeURIComponent(outlet.id)+"/insights",{signal:controller.signal})
   .then(async r=>{
    if(!r.ok)throw new Error("The database returned "+r.status);
    return r.json();
   })
   .then(v=>{cache.current[outlet.id]=v;setData(v);setLoading(false);})
   .catch(e=>{if(!controller.signal.aborted){setError(e.message||"Unable to load performance data");setLoading(false);}});
  return ()=>controller.abort();
 },[apiBase,outlet?.id,reload]);

 const history=data?.history||[];
 const selectedHistory=useMemo(()=>{
  if(period==="6 months")return history.slice(-6);
  if(period==="12 months")return history.slice(-12);
  return history;
 },[history,period]);
 const graph=useMemo(()=>selectedHistory.map(m=>({
  period:m.month,label:labelMonth(m.month),
  volume:Number(m.volume_kes),count:Number(m.transaction_count),ticket:Number(m.average_ticket_kes)
 })),[selectedHistory]);
 const filteredRecent=useMemo(()=>data?.recent_transactions?.filter(t=>(t.id+" "+t.kind+" "+t.timestamp).toLowerCase().includes(transactionsSearch.toLowerCase()))||[],[data,transactionsSearch]);
 const summary=data?.summary;
 const isCritical=outlet?.status==="Critical";
 const volumeGrowth=summary?.volume_growth_pct;
 const showGrowth=volumeGrowth!==null&&volumeGrowth!==undefined;
 const statColors=metric==="count"?"#36bbec":metric==="ticket"?"#ffb368":"#ff5474";
 const graphDataKey=metric==="count"?"count":metric==="ticket"?"ticket":"volume";
 const displayChartValue=n=>metric==="count"?NUM(n):KES(n);
 const exportCsv=()=>{
  if(!history.length)return;
  const csv=[["Month","Transaction Count (synthetic)","Volume KES (synthetic)","Average Ticket KES (synthetic)"],
   ...history.map(h=>[h.month,h.transaction_count,h.volume_kes,h.average_ticket_kes])]
  .map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(",")).join("\n");
  const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
  const a=document.createElement("a");a.href=url;a.download="agentpulse_"+outlet.id+"_monthly_synthetic.csv";a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
 };
 return <aside className="ap-outlet-insights" role="region" aria-label={"Outlet performance dashboard for "+(outlet?.name||"selected outlet")}>
  <div className="ap-in-header">
   <div className="ap-in-overline"><span/> AGENT PERFORMANCE / {outlet?.id}</div>
   <button className="ap-in-close" onClick={onClose} title="Close outlet dashboard" aria-label="Close outlet dashboard"><X size={18}/></button>
   <div className="ap-in-title">
    <div><h2>{outlet?.name}</h2><p><MapPin size={12}/>{outlet?.area}, Nairobi <span className={"ap-in-health "+(isCritical?"critical":outlet?.status==="Watch"?"watch":"healthy")}>{outlet?.status}</span></p></div>
    <span className="ap-in-live"><Activity size={13}/> Database profile</span>
   </div>
   <div className="ap-in-tabs">{["Overview","Trends","Transactions"].map(t=><button key={t} className={tab===t?"active":""} onClick={()=>setTab(t)}>{t}</button>)}</div>
  </div>

  <div className="ap-in-scroll">
   {loading?<div className="ap-in-loading"><div className="ap-in-loader"/><h3>Loading performance history</h3><p>Retrieving monthly records from Railway PostgreSQL</p></div>:error?<div className="ap-in-error"><Info size={25}/><h3>History is unavailable</h3><p>{error}</p><button onClick={()=>setReload(x=>x+1)}><RefreshCw size={14}/> Retry</button></div>:data&&<>
    <div className="ap-in-period"><CalendarRange size={15}/><div><b>{labelMonth(data.period.first)} to {labelMonth(data.period.last)}</b><small>{data.period.months} months of modelled performance</small></div><button onClick={exportCsv} aria-label="Export outlet monthly trend"><Download size={15}/></button></div>

    {tab!=="Transactions"&&<>
     <div className="ap-in-metrics">
      <Metric icon={BarChart3} label="Since start · transactions" value={NUM(summary?.total_modelled_transactions)} sub="Aggregated monthly model" color="red"/>
      <Metric icon={TrendingUp} label="Since start · value" value={KES(summary?.total_modelled_volume_kes)} sub="Aggregated monthly model" color="blue"/>
      <Metric icon={Wallet} label="Current cash" value={KES(outlet?.cash)} sub="Current demo balance" color="teal"/>
      <Metric icon={WalletCards} label="Current e-float" value={KES(outlet?.float)} sub="Current demo balance" color="amber"/>
     </div>
     <div className="ap-in-card ap-in-chartcard">
      <div className="ap-in-chartheading">
       <div><h3>Transaction performance</h3><p>{metric==="value"?"Monthly transaction value":metric==="count"?"Monthly transaction count":"Average transaction value"} · from stored model</p></div>
       <div className="ap-in-growth"><span className={showGrowth&&volumeGrowth>=0?"up":"down"}>{showGrowth&&volumeGrowth>=0?<ArrowUpRight size={13}/>:<ArrowDownRight size={13}/>} {pctText(volumeGrowth)}</span><small>Value vs previous month</small></div>
      </div>
      <div className="ap-in-chartcontrols">
       <div className="ap-in-chartmetrics">{[["value","Value"],["count","Count"],["ticket","Avg. ticket"]].map(([key,name])=><button key={key} onClick={()=>setMetric(key)} className={metric===key?"active":""}>{name}</button>)}</div>
       <label className="ap-in-periodpicker"><Clock3 size={13}/><select aria-label="Trend reporting window" value={period} onChange={e=>setPeriod(e.target.value)}><option>6 months</option><option>12 months</option><option>All 36 months</option></select><ChevronDown size={12}/></label>
      </div>
      <div className="ap-in-chart">
       <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={graph} margin={{top:9,left:3,right:4,bottom:0}}>
         <defs><linearGradient id="ap-outlet-chart-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={statColors} stopOpacity=".38"/><stop offset="1" stopColor={statColors} stopOpacity="0"/></linearGradient></defs>
         <CartesianGrid vertical={false} stroke="#243449" strokeDasharray="3 6"/>
         <XAxis dataKey="label" tick={{fontSize:9,fill:"#869eb2"}} tickLine={false} axisLine={false} minTickGap={22} interval="preserveStartEnd"/>
         <YAxis tick={{fontSize:9,fill:"#869eb2"}} tickLine={false} axisLine={false} tickFormatter={SHORT} width={43}/>
         <Tooltip {...chartTooltip} formatter={v=>[displayChartValue(v),metric==="count"?"Monthly transactions":metric==="ticket"?"Average ticket":"Monthly value"]}/>
         <Area type="monotone" dataKey={graphDataKey} stroke={statColors} fill="url(#ap-outlet-chart-fill)" strokeWidth={2.6} dot={false} activeDot={{r:4,strokeWidth:2,stroke:"#0c1a29"}} animationDuration={650}/>
        </AreaChart>
       </ResponsiveContainer>
      </div>
      <div className="ap-in-chartperiod"><span>{graph[0]?.label}</span><span>{graph[graph.length-1]?.label}</span></div>
     </div>
     <div className="ap-in-mini-grid">
      <div><small>Latest month · transactions</small><b>{NUM(summary?.latest_month?.transaction_count)}</b><span>{pctText(summary?.transaction_growth_pct)} vs previous</span></div>
      <div><small>Latest month · transaction value</small><b>{KES(summary?.latest_month?.volume_kes)}</b><span>{pctText(summary?.volume_growth_pct)} vs previous</span></div>
     </div>
    </>}

    {(tab==="Overview"||tab==="Transactions")&&<>
     <div className="ap-in-card">
      <div className="ap-in-card-title"><div><h3>Recent transaction sample</h3><p>Posted event records, not the complete monthly ledger</p></div><span>{summary?.recent_posted_event_count} events</span></div>
      {tab==="Transactions"&&<input className="ap-in-search" placeholder="Search type, date or transaction ID" aria-label="Search outlet sample transactions" value={transactionsSearch} onChange={e=>setTransactionsSearch(e.target.value)}/>}
      <div className="ap-in-transactions">{filteredRecent.slice(0,tab==="Transactions"?40:5).map(t=><div key={t.id}><span className={"ap-in-transaction-icon "+(t.kind==="Withdrawal"?"withdrawal":"deposit")}><ReceiptText size={16}/></span><div><b>{t.kind}</b><small>{new Date(t.timestamp).toLocaleDateString("en-KE",{day:"numeric",month:"short",year:"numeric"})} · {t.id}</small></div><strong>{KES(t.amount_kes)}</strong></div>)}{!filteredRecent.length&&<p className="ap-in-none">No matching transaction samples.</p>}</div>
     </div>
    </>}

    <div className="ap-in-caveat"><Info size={14}/><p><b>Demonstration data:</b> {data.caveat} Monthly trends and recent event commissions are different synthetic datasets. Exact storefronts require verified coordinates.</p></div>
   </>}
  </div>
 </aside>;
}
