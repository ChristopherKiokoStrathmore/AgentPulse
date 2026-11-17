const {test,expect}=require("@playwright/test");

test("overview risk alert opens actionable Nairobi incident map",async ({page})=>{
 await page.goto("/");
 await expect(page.locator(".ap-livehero")).toBeVisible();
 await expect(page.getByRole("button",{name:/investigate risks/i})).toBeVisible();
 await page.getByRole("button",{name:/investigate risks/i}).click();
 const dialog=page.getByRole("dialog",{name:"Liquidity incident command map"});
 await expect(dialog).toBeVisible();
 await expect(dialog.getByText("LIQUIDITY COMMAND")).toBeVisible();
 await expect(dialog.locator(".ap-incident-list-item").first()).toBeVisible();
 await expect(dialog.getByRole("button",{name:"Street level"})).toBeVisible();
 await dialog.getByRole("button",{name:"Network"}).click();
 await expect(dialog.getByRole("button",{name:"Network"})).toHaveClass(/active/);
 await dialog.locator(".ap-incident-list-item").first().click();
 await expect(dialog.locator(".ap-inspection-issue")).toBeVisible();
 const link=dialog.getByRole("link",{name:/open google street view/i});
 await expect(link).toHaveAttribute("href",/google\.com\/maps\/@\?api=1&map_action=pano/);
 await page.keyboard.press("Escape");
 await expect(dialog.getByRole("region",{name:/outlet performance dashboard/i})).toHaveCount(0);
 await page.keyboard.press("Escape");
 await expect(dialog).toHaveCount(0);
});

test("all overview risk hotspot buttons open the incident drawer",async ({page})=>{
 await page.goto("/");
 const dots=page.locator(".ap-livehero-dot.is-risk");
 await expect(dots.first()).toBeVisible();
 await dots.first().click();
 await expect(page.getByRole("dialog",{name:"Liquidity incident command map"})).toBeVisible();
});


test("switch map styles, maximize map, and open 36 month outlet trends",async ({page})=>{
 const history=Array.from({length:36},(_,i)=>{
  const month=new Date(Date.UTC(2023,10+i,1)).toISOString().slice(0,7);
  const count=1000+i*19;
  return {month,transaction_count:count,volume_kes:count*1300,average_ticket_kes:1300};
 });
 await page.route("**/v1/outlets/*/insights",async route=>{
  const id=route.request().url().split("/").at(-2);
  await route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({
   source:"synthetic",
   outlet:{id,name:"Test outlet"},
   period:{first:"2023-11",last:"2026-10",months:36},
   history,
   summary:{
    total_modelled_transactions:history.reduce((a,h)=>a+h.transaction_count,0),
    total_modelled_volume_kes:history.reduce((a,h)=>a+h.volume_kes,0),
    latest_month:history.at(-1),
    transaction_growth_pct:1.1,
    volume_growth_pct:1.1,
    recent_posted_event_count:2,
    recent_posted_event_commission_kes:100
   },
   recent_transactions:[
    {id:"SIM-001",timestamp:"2026-10-30T12:00:00Z",kind:"Deposit",amount_kes:2000,commission_kes:12,status:"Completed"},
    {id:"SIM-002",timestamp:"2026-10-29T12:00:00Z",kind:"Withdrawal",amount_kes:1500,commission_kes:9,status:"Completed"}
   ],
   caveat:"These synthetic monthly totals are not reconstructed from posted event samples."
  })});
 });
 await page.goto("/");
 await page.getByRole("button",{name:/investigate risks/i}).click();
 const dialog=page.getByRole("dialog",{name:"Liquidity incident command map"});
 const style=dialog.getByLabel("Map style");
 await expect(style).toHaveValue("Streets");
 await style.selectOption("Light");
 await expect(style).toHaveValue("Light");
 await style.selectOption("Terrain");
 await expect(style).toHaveValue("Terrain");
 await dialog.getByRole("button",{name:"Expand map to full screen"}).click();
 await expect(dialog.locator(".ap-incident-window")).toHaveClass(/ap-map-maximized/);
 await dialog.getByRole("button",{name:"Exit full screen map"}).click();
 await expect(dialog.locator(".ap-incident-window")).not.toHaveClass(/ap-map-maximized/);
 await dialog.locator(".ap-incident-list-item").first().click();
 const insights=dialog.getByRole("region",{name:/Outlet performance dashboard/i});
 await expect(insights).toBeVisible();
 await page.waitForTimeout(2500);
 console.log("OUTLET_INSIGHTS_DIAG:",JSON.stringify((await insights.innerText()).slice(0,2400)));
 await expect(insights.getByText("36 months of modelled performance")).toBeVisible({timeout:10000});
 await expect(insights.getByText("Transaction performance")).toBeVisible();
 await expect(insights.locator(".recharts-responsive-container").first()).toBeVisible();
 await insights.getByRole("button",{name:"Trends"}).click();
 await insights.getByLabel("Trend reporting window").selectOption("6 months");
 await expect(insights.getByText("6 months of modelled performance")).toHaveCount(0);
 await expect(insights.getByText("Transaction performance")).toBeVisible();
 await insights.getByRole("button",{name:"Transactions"}).click();
 await expect(insights.getByText("SIM-001")).toBeVisible();
 await insights.getByRole("button",{name:"Close outlet dashboard"}).click();
 await expect(insights).toHaveCount(0);
});
