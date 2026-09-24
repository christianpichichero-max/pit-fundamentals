#!/usr/bin/env node

/**
 * Build the deliberately small public proof pack from a reviewed full sample CSV.
 *
 * Usage:
 *   node scripts/build_public_proof.mjs path/to/reviewed-full-sample.csv
 *
 * This is not a product data export. It keeps five recognizable companies and
 * each company's latest three fiscal years so prospects can inspect the schema,
 * filing timestamps, QA flags, and restatement representation without receiving
 * a useful multi-cycle historical database for free.
 */

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const source = process.argv[2];
if (!source) {
  throw new Error("Pass the reviewed source CSV path.");
}

const targetTickers = new Set(["AAPL", "HON", "NFLX", "NVDA", "WMT"]);
const input = readFileSync(resolve(source), "utf8").trimEnd().split(/\r?\n/);
const header = input[0];
const headers = header.split(",");
const tickerIndex = headers.indexOf("ticker");
const yearIndex = headers.indexOf("fiscal_year");
if (tickerIndex < 0 || yearIndex < 0) throw new Error("Source is missing ticker or fiscal_year.");

const parsed = input.slice(1).map((line) => ({ line, fields: line.split(",") }));
const yearsByTicker = new Map();
for (const row of parsed) {
  const ticker = row.fields[tickerIndex];
  if (!targetTickers.has(ticker)) continue;
  const years = yearsByTicker.get(ticker) ?? new Set();
  years.add(Number(row.fields[yearIndex]));
  yearsByTicker.set(ticker, years);
}

const allowedYears = new Map(
  [...yearsByTicker].map(([ticker, years]) => [
    ticker,
    new Set([...years].sort((a, b) => b - a).slice(0, 3)),
  ]),
);

const output = parsed
  .filter((row) => allowedYears.get(row.fields[tickerIndex])?.has(Number(row.fields[yearIndex])))
  .map((row) => row.line);

if (allowedYears.size !== targetTickers.size) {
  throw new Error(`Expected ${targetTickers.size} companies, found ${allowedYears.size}.`);
}

const target = resolve("data/pit_fundamentals_history.csv");
writeFileSync(target, `${header}\n${output.join("\n")}\n`, "utf8");
console.log(`Wrote ${output.length} rows to ${target}`);
for (const [ticker, years] of [...allowedYears].sort()) {
  console.log(`${ticker}: ${[...years].sort((a, b) => a - b).join(", ")}`);
}
