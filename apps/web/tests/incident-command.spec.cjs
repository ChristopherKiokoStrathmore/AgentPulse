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
 await expect(dialog).toHaveCount(0);
});

test("all overview risk hotspot buttons open the incident drawer",async ({page})=>{
 await page.goto("/");
 const dots=page.locator(".ap-livehero-dot.is-risk");
 await expect(dots.first()).toBeVisible();
 await dots.first().click();
 await expect(page.getByRole("dialog",{name:"Liquidity incident command map"})).toBeVisible();
});
