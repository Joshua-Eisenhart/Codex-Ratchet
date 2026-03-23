import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { chromium } from "playwright";

function parseArgs(argv) {
  const args = {
    zip: null,
    doc: null,
    sendTextFile: null,
    downloadDir: null,
    profileDir: null,
    headed: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--headed") args.headed = true;
    else if (a === "--zip") args.zip = argv[++i];
    else if (a === "--doc") args.doc = argv[++i];
    else if (a === "--send-text-file") args.sendTextFile = argv[++i];
    else if (a === "--download-dir") args.downloadDir = argv[++i];
    else if (a === "--profile-dir") args.profileDir = argv[++i];
    else throw new Error(`Unknown arg: ${a}`);
  }
  for (const k of ["zip", "doc", "sendTextFile", "downloadDir", "profileDir"]) {
    if (!args[k]) throw new Error(`Missing required arg --${k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase())}`);
  }
  return args;
}

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

async function waitForEnter(promptText) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  await new Promise((resolve) => rl.question(promptText, () => resolve()));
  rl.close();
}

async function main() {
  const args = parseArgs(process.argv);

  const zipPath = path.resolve(args.zip);
  const docPath = path.resolve(args.doc);
  const sendText = fs.readFileSync(path.resolve(args.sendTextFile), "utf8").trim();
  const downloadDir = path.resolve(args.downloadDir);
  const profileDir = path.resolve(args.profileDir);

  if (!fs.existsSync(zipPath)) throw new Error(`ZIP not found: ${zipPath}`);
  if (!fs.existsSync(docPath)) throw new Error(`Doc not found: ${docPath}`);

  ensureDir(downloadDir);
  ensureDir(profileDir);

  const context = await chromium.launchPersistentContext(profileDir, {
    headless: !args.headed,
    acceptDownloads: true,
    viewport: { width: 1280, height: 900 },
  });

  const page = context.pages()[0] ?? (await context.newPage());

  // Capture downloads regardless of how the user clicks (automation or manual).
  page.on("download", async (download) => {
    const suggested = download.suggestedFilename();
    const dest = path.join(downloadDir, suggested);
    await download.saveAs(dest);
    process.stdout.write(`\nDOWNLOADED: ${dest}\n`);
  });

  await page.goto("https://chatgpt.com/", { waitUntil: "domcontentloaded" });

  // If not logged in, user must log in manually (no password in code).
  // Heuristic: prompt textarea exists when logged in.
  const textarea = page.locator("textarea");
  const loggedIn = await textarea.first().isVisible().catch(() => false);
  if (!loggedIn) {
    process.stdout.write("\nNot logged in (no prompt textarea visible). Please log in manually in the opened browser.\n");
    await waitForEnter("After login completes and you see the chat input box, press Enter here to continue...");
  }

  // Create a new chat (best-effort).
  // ChatGPT UI changes frequently; keep this resilient.
  await page.goto("https://chatgpt.com/", { waitUntil: "domcontentloaded" });

  // Attach ZIP + doc. ChatGPT uses hidden file inputs; we try the first visible input[type=file].
  // If this fails, user can attach manually; script will still send the text.
  try {
    const fileInputs = page.locator('input[type="file"]');
    const count = await fileInputs.count();
    if (count === 0) throw new Error("no_file_input");
    await fileInputs.first().setInputFiles([zipPath, docPath]);
  } catch (err) {
    process.stdout.write(`\nWARN: auto-attach failed (${String(err)}). Please attach the ZIP + doc manually, then press Enter.\n`);
    await waitForEnter("Press Enter after attaching both files...");
  }

  // Fill send text.
  await textarea.first().click();
  await textarea.first().fill(sendText);

  // Send (best-effort).
  const sendButton = page.locator('button[data-testid="send-button"],button[aria-label*="Send"],button:has-text("Send")');
  const canSend = await sendButton.first().isVisible().catch(() => false);
  if (canSend) {
    await sendButton.first().click();
  } else {
    process.stdout.write("\nWARN: could not find Send button selector. Please press Enter after you send the message manually.\n");
    await waitForEnter("Press Enter after sending...");
  }

  process.stdout.write("\nWaiting for a .zip download to be triggered. If ChatGPT returns a ZIP, click its download button.\n");
  process.stdout.write(`Downloads will be saved under: ${downloadDir}\n`);
  process.stdout.write("When done, close the browser window to exit.\n");

  // Keep process alive until user closes browser.
  await context.waitForEvent("close");
}

main().catch((err) => {
  process.stderr.write(`${err?.stack ?? String(err)}\n`);
  process.exit(1);
});

