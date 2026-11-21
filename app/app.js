// app.js - Loads app/judges.json and renders the searchable clerkship guide.
"use strict";

let JUDGES = [];
let current = [];

const el = {
  search: document.getElementById("search"),
  hiring: document.getElementById("f-hiring"),
  level: document.getElementById("f-level"),
  results: document.getElementById("results"),
  detail: document.getElementById("detail"),
  stats: document.getElementById("stats"),
};

function badgeFor(j) {
  const cls = j.hiring ? "hiring" : "not-hiring";
  const text = j.hiring ? "Hiring" : "Not hiring";
  const levelCls = j.level === "circuit" ? "circuit" : "district";
  const levelTxt = j.level === "circuit" ? "Circuit" : "District";
  return (
    `<span class="badge ${cls}">${text}</span>` +
    `<span class="badge ${levelCls}">${levelTxt}</span>`
  );
}

function freshnessClass(f) {
  if (f === "fresh") return "yes";
  if (f === "recent") return "yes recent";
  if (f === "stale") return "yes stale";
  return "yes";
}

function applyFilters() {
  const q = el.search.value.trim().toLowerCase();
  const hire = el.hiring.checked;
  const level = el.level.value;

  current = JUDGES.filter((j) => {
    if (hire && !j.hiring) return false;
    if (level && j.level !== level) return false;
    if (!q) return true;
    const hay = [
      j.judge,
      j.court,
      j.duty_station,
      j.appointed_by,
      j.education,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return hay.includes(q);
  });

  renderList();
}

function renderList() {
  el.results.innerHTML = "";
  if (current.length === 0) {
    const li = document.createElement("li");
    li.innerHTML = '<span class="muted">No judges match your search.</span>';
    el.results.appendChild(li);
    return;
  }

  for (const j of current) {
    const li = document.createElement("li");
    li.innerHTML =
      `<div class="name">${j.judge} ${badgeFor(j)}</div>` +
      `<div class="sub">${j.court || ""}${j.duty_station ? " &middot; " + j.duty_station : ""}</div>`;
    li.addEventListener("click", () => {
      document.querySelectorAll(".results li.active").forEach((n) => n.classList.remove("active"));
      li.classList.add("active");
      showDetail(j);
    });
    el.results.appendChild(li);
  }
}

function esc(s) {
  if (!s) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function kv(label, value) {
  if (!value) return "";
  return `<dt>${esc(label)}</dt><dd>${esc(value)}</dd>`;
}

function showDetail(j) {
  const hiringClass = j.hiring ? freshnessClass(j.freshness) : "";
  const hiringHeading = j.hiring ? "Hiring clerks" : "Not currently hiring";
  const hireDetail = j.hiring
    ? [
        kv("Term", j.hiring_term),
        kv("Freshness", j.freshness),
        kv("Posting date", j.posting_date),
      ].join("")
    : "";

  const facts = [
    kv("Title", j.title),
    kv("Court", j.court),
    kv("Courthouse", j.courthouse),
    kv("Duty station", j.duty_station),
    kv("Appointed by", j.appointed_by),
    kv("Party", j.party),
    kv("Born", j.born),
    kv("Years on bench", j.years_of_service),
    kv("Nomination", j.nomination_date),
    kv("Confirmation vote", j.confirmation_vote),
    kv("Education", j.education),
  ].join("");

  const links = [
    j.oscar_search_url
      ? `<a href="${esc(j.oscar_search_url)}" target="_blank" rel="noopener">OSCAR clerkships</a>`
      : "",
    j.scholar_url
      ? `<a href="${esc(j.scholar_url)}" target="_blank" rel="noopener">Google Scholar</a>`
      : "",
    j.wikipedia_url
      ? `<a href="${esc(j.wikipedia_url)}" target="_blank" rel="noopener">Wikipedia</a>`
      : "",
  ]
    .filter(Boolean)
    .join("");

  const bio = j.wikipedia_summary
    ? `<p class="bio">${esc(j.wikipedia_summary)}</p>`
    : "";

  el.detail.classList.remove("hidden");
  el.detail.innerHTML = `
    <h2>${esc(j.judge)}</h2>
    <p class="court">${esc(j.court || "")}</p>
    <div class="hiring-box ${hiringClass}">
      <h3>${hiringHeading}</h3>
      <dl class="kv">${hireDetail}</dl>
    </div>
    <dl class="kv">${facts}</dl>
    ${bio}
    <div class="links">${links}</div>
  `;
}

async function load() {
  try {
    const res = await fetch("judges.json");
    const data = await res.json();
    JUDGES = data.judges;
    const c = data.counts;
    el.stats.textContent =
      `${c.total} judges (${c.district} district, ${c.circuit} circuit) ` +
      `&middot; ${c.hiring} currently hiring ` +
      `&middot; generated ${data.generated_at}`;
    el.stats.innerHTML = el.stats.textContent;
    applyFilters();
  } catch (e) {
    el.stats.textContent = "Failed to load judges.json. Run export_site_data.py first.";
  }
}

el.search.addEventListener("input", applyFilters);
el.hiring.addEventListener("change", applyFilters);
el.level.addEventListener("change", applyFilters);

load();