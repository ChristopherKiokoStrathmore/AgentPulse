const {defineConfig}=require("@playwright/test");
module.exports=defineConfig({
 testDir:"./tests",
 timeout:45000,
 retries:process.env.CI?1:0,
 reporter:"line",
 use:{baseURL:"http://127.0.0.1:3000",headless:true,viewport:{width:1440,height:900},screenshot:"only-on-failure"},
 webServer:{command:"npm run start -- -p 3000",url:"http://127.0.0.1:3000",timeout:120000,reuseExistingServer:!process.env.CI}
});
