// Кросс-платформенный дамп news.js -> JSON (замена macOS-специфичного JXA в build.sh).
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
global.window = {};
const src = fs.readFileSync(path.join(root, "news.js"), "utf8");
// eslint-disable-next-line no-eval
eval(src);

fs.writeFileSync(path.join(root, "tools", "news.json"), JSON.stringify(window.NEWS), "utf8");
console.log("news.json written:", window.NEWS.length, "articles");
