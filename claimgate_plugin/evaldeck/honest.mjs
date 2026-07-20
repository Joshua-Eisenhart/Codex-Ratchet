import fs from "node:fs";
const r = JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
const bad = (r.verdict==="INTEGRATED"||r.verdict==="PASS") && r.pass!==true;
process.exit(bad ? 1 : 0);
