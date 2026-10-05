// =========================================================
// JobSpot – the JavaScript for the web page.
//
// What this file does:
// 1. Reacts to clicks and typing (search, filters, save, status buttons).
// 2. Asks our own local server for data with fetch() (for example /api/jobs).
// 3. Builds the job cards and puts them on the page.
//
// Safety: we always put job text on the page with "textContent", never
// with "innerHTML". textContent shows text as plain text, so a job title
// can never contain code that runs in the page.
// =========================================================


// ---------- Things we remember while the page is open ----------

// The last search, so "Show more jobs" and "Try again" can repeat it
let lastSearch = null;

// Which page of results we showed last (1 = first page)
let currentPage = 1;

// The saved jobs, by id. Lets us show "Saved" on the right cards.
// Example: savedJobsById["jobsuche:123"] = { id: "jobsuche:123", title: "Barista", ... }
let savedJobsById = {};

// Words for each status, as shown on screen
const STATUS_LABELS = {
  saved: "Saved",
  applied: "Applied",
  replied: "Got a reply",
  interview: "Interview",
  rejected: "Rejected",
};

// The order of the status buttons on a saved job card
const STATUS_ORDER = ["saved", "applied", "replied", "interview", "rejected"];

// Words for each job type
const JOB_TYPE_LABELS = {
  full_time: "Full-time",
  part_time: "Part-time",
  full_or_part_time: "Full- or part-time",
  not_stated: "",
};

// Shown when our own local server does not answer at all
const MESSAGE_APP_NOT_RUNNING =
  "JobSpot has stopped. Please close this tab and start JobSpot again.";


// ---------- Small helper: find an element by its id ----------

function byId(id) {
  return document.getElementById(id);
}


// =========================================================
// Talking to our server
// =========================================================

// Sends a request to our local server and gives back the answer as an object.
// If something goes wrong, it throws an Error with a friendly message.
//
// "async" means this function can wait for slow things (like the network)
// without freezing the page. "await" is where it waits.
async function callServer(method, url, body) {
  const options = { method: method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, options);
  } catch (error) {
    // fetch() only fails like this when the server cannot be reached at all
    throw new Error(MESSAGE_APP_NOT_RUNNING);
  }

  // 204 means "done, nothing to send back"
  if (response.status === 204) {
    return null;
  }

  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  if (!response.ok) {
    // Our server always sends a friendly sentence in "message"
    if (data !== null && data.message) {
      throw new Error(data.message);
    }
    throw new Error("Something went wrong. Please try again.");
  }

  return data;
}


// =========================================================
// Switching between "Find jobs" and "Saved jobs"
// =========================================================

function showView(viewName) {
  const searchView = byId("view-search");
  const savedView = byId("view-saved");
  const searchNav = byId("nav-search");
  const savedNav = byId("nav-saved");

  if (viewName === "saved") {
    searchView.hidden = true;
    savedView.hidden = false;
    searchNav.classList.remove("is-active");
    savedNav.classList.add("is-active");
    // Remember the page in the address bar, so a refresh stays here
    history.replaceState(null, "", "#saved");
    loadSavedJobs();
  } else {
    searchView.hidden = false;
    savedView.hidden = true;
    searchNav.classList.add("is-active");
    savedNav.classList.remove("is-active");
    history.replaceState(null, "", location.pathname + location.search);
    // The saved state of cards may have changed on the other page
    refreshSaveButtons();
  }
  window.scrollTo(0, 0);
}


// =========================================================
// Dark mode
// =========================================================

function isDarkMode() {
  return document.documentElement.getAttribute("data-theme") === "dark";
}

function setTheme(themeName) {
  document.documentElement.setAttribute("data-theme", themeName);
  const button = byId("theme-button");
  if (themeName === "dark") {
    button.setAttribute("aria-label", "Switch to light mode");
  } else {
    button.setAttribute("aria-label", "Switch to dark mode");
  }
}

function setupTheme() {
  // Did the person pick a mode before? (see the small script in index.html)
  let savedTheme = null;
  try {
    savedTheme = localStorage.getItem("jobspot-theme");
  } catch (error) {
    savedTheme = null;
  }

  const computerSetting = window.matchMedia("(prefers-color-scheme: dark)");

  if (savedTheme === "light" || savedTheme === "dark") {
    setTheme(savedTheme);
  } else if (computerSetting.matches) {
    setTheme("dark");
  } else {
    setTheme("light");
  }

  // If the computer setting changes and the person never picked a mode, follow it
  computerSetting.addEventListener("change", function (event) {
    let picked = null;
    try {
      picked = localStorage.getItem("jobspot-theme");
    } catch (error) {
      picked = null;
    }
    if (picked === null) {
      if (event.matches) {
        setTheme("dark");
      } else {
        setTheme("light");
      }
    }
  });

  // The moon/sun button
  byId("theme-button").addEventListener("click", function () {
    let newTheme = "dark";
    if (isDarkMode()) {
      newTheme = "light";
    }
    setTheme(newTheme);
    try {
      localStorage.setItem("jobspot-theme", newTheme);
    } catch (error) {
      // Storage not allowed: the mode still changes, it is just not remembered
    }
  });
}


// =========================================================
// Searching
// =========================================================

// Reads the search box and the filters into one object
function readSearchForm() {
  return {
    what: byId("what-input").value.trim(),
    where: byId("where-input").value.trim(),
    distance: byId("distance-filter").value,
    jobType: byId("job-type-filter").value,
    postedDays: byId("posted-filter").value,
  };
}

// Builds the address for our search route, for example
// /api/jobs?what=Barista&where=Berlin&distance=25&job_type=any&page=1
function buildSearchUrl(search, page) {
  const params = new URLSearchParams();
  params.set("what", search.what);
  params.set("where", search.where);
  params.set("distance", search.distance);
  params.set("job_type", search.jobType);
  if (search.postedDays !== "") {
    params.set("posted_days", search.postedDays);
  }
  params.set("page", page);
  return "/api/jobs?" + params.toString();
}

function showFormMessage(text) {
  const message = byId("form-message");
  if (text === "") {
    message.hidden = true;
    message.textContent = "";
  } else {
    message.hidden = false;
    message.textContent = text;
  }
}

// Runs when the person presses "Search jobs" (or changes a filter)
function startNewSearch() {
  const search = readSearchForm();

  if (search.where === "") {
    showFormMessage("Please tell us where you'd like to work, for example a town or a postcode.");
    byId("where-input").focus();
    return;
  }
  showFormMessage("");

  lastSearch = search;
  currentPage = 1;
  saveSearchInAddressBar(search);
  runSearch(1);
}

// Asks the server for one page of jobs and shows them.
// page 1 = a new search (replace the cards), page 2+ = add more cards.
async function runSearch(page) {
  const isFirstPage = page === 1;

  byId("how-it-works").hidden = true;
  byId("results").hidden = false;
  byId("no-results").hidden = true;
  byId("search-error").hidden = true;
  byId("show-more").hidden = true;

  if (isFirstPage) {
    byId("job-grid").replaceChildren();
    byId("results-title").textContent = "";
    byId("results-subtitle").textContent = "";
    byId("loading").hidden = false;
    // Scroll down to where the results will appear
    byId("results").scrollIntoView({ behavior: "smooth", block: "start" });
  } else {
    byId("show-more").hidden = false;
    byId("show-more").disabled = true;
    byId("show-more").textContent = "Loading more jobs…";
  }

  let result;
  try {
    result = await callServer("GET", buildSearchUrl(lastSearch, page));
  } catch (error) {
    byId("loading").hidden = true;
    byId("show-more").disabled = false;
    byId("show-more").textContent = "Show more jobs";
    showSearchError(error.message, isFirstPage);
    return;
  }

  byId("loading").hidden = true;
  currentPage = page;
  showResults(result, isFirstPage);
}

function showSearchError(text, isFirstPage) {
  if (isFirstPage) {
    byId("results-title").textContent = "";
    byId("results-subtitle").textContent = "";
    byId("search-error").hidden = false;
    byId("search-error-text").textContent = text;
  } else {
    // Keep the jobs we already have; just show the message under them
    byId("show-more").hidden = false;
    showFormMessage(text);
  }
}

function showResults(result, isFirstPage) {
  // Title, for example "24 jobs near Berlin"
  let jobWord = "jobs";
  if (result.total === 1) {
    jobWord = "job";
  }
  const totalText = result.total.toLocaleString("en-US");
  byId("results-title").textContent = totalText + " " + jobWord + " near " + result.place;
  byId("results-subtitle").textContent = buildSubtitle(lastSearch);

  if (isFirstPage && result.jobs.length === 0) {
    byId("no-results").hidden = false;
    // Only offer "Widen my search" if there is something we can widen
    byId("widen-search").hidden = !canWidenSearch();
    return;
  }

  // Make one card per job and add it to the grid
  const grid = byId("job-grid");
  for (const job of result.jobs) {
    grid.appendChild(createJobCard(job));
  }

  const moreButton = byId("show-more");
  moreButton.disabled = false;
  moreButton.textContent = "Show more jobs";
  moreButton.hidden = !result.has_more;
}

// For example "Within 25 km · Part-time · Last 7 days · newest first"
function buildSubtitle(search) {
  const parts = ["Within " + search.distance + " km"];
  if (search.jobType === "part_time") {
    parts.push("Part-time");
  } else if (search.jobType === "full_time") {
    parts.push("Full-time");
  }
  if (search.postedDays === "1") {
    parts.push("Last 24 hours");
  } else if (search.postedDays !== "") {
    parts.push("Last " + search.postedDays + " days");
  }
  parts.push("newest first");
  return parts.join(" · ");
}

function canWidenSearch() {
  const search = readSearchForm();
  if (search.distance !== "100") {
    return true;
  }
  if (search.jobType !== "any") {
    return true;
  }
  if (search.postedDays !== "") {
    return true;
  }
  return false;
}

// "Widen my search": biggest distance, no other filters, search again
function widenSearch() {
  byId("distance-filter").value = "100";
  byId("job-type-filter").value = "any";
  byId("posted-filter").value = "";
  startNewSearch();
}

function clearFilters() {
  byId("distance-filter").value = "25";
  byId("job-type-filter").value = "any";
  byId("posted-filter").value = "";
  // If there are results on screen, show them again without filters
  if (lastSearch !== null) {
    startNewSearch();
  }
}

// Puts the search into the address bar (for example ?what=Barista&where=Berlin),
// so a refresh or a bookmark shows the same search again.
function saveSearchInAddressBar(search) {
  const params = new URLSearchParams();
  params.set("what", search.what);
  params.set("where", search.where);
  if (search.distance !== "25") {
    params.set("distance", search.distance);
  }
  if (search.jobType !== "any") {
    params.set("job_type", search.jobType);
  }
  if (search.postedDays !== "") {
    params.set("posted_days", search.postedDays);
  }
  history.replaceState(null, "", "?" + params.toString());
}

// When the page opens with a search in the address bar, fill the form and run it
function loadSearchFromAddressBar() {
  const params = new URLSearchParams(location.search);
  const where = params.get("where");
  if (where === null || where === "") {
    return false;
  }
  byId("where-input").value = where;
  byId("what-input").value = params.get("what") || "";
  setSelectValue("distance-filter", params.get("distance"));
  setSelectValue("job-type-filter", params.get("job_type"));
  setSelectValue("posted-filter", params.get("posted_days"));
  startNewSearch();
  return true;
}

// Only choose a value if it is one of the options in the list
function setSelectValue(selectId, value) {
  if (value === null) {
    return;
  }
  const select = byId(selectId);
  for (const option of select.options) {
    if (option.value === value) {
      select.value = value;
    }
  }
}


// =========================================================
// Building job cards
// =========================================================

// Makes a new element, for example makeElement("p", "job-company", "Café Mühle")
function makeElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  if (text !== undefined) {
    element.textContent = text;
  }
  return element;
}

// Two letters for the little logo square, for example "Café Mühle" → "CM"
function getInitials(job) {
  let name = job.company;
  if (name === "") {
    name = job.title;
  }
  const words = name.split(" ");
  let initials = "";
  for (const word of words) {
    // Only use words that start with a letter (skip "&", "(m/w/d)", ...)
    const firstLetter = word.charAt(0);
    if (firstLetter.toLowerCase() !== firstLetter.toUpperCase()) {
      initials = initials + firstLetter.toUpperCase();
    }
    if (initials.length === 2) {
      break;
    }
  }
  if (initials === "") {
    initials = "?";
  }
  return initials;
}

// "Today", "Yesterday", "3 days ago" ...
function formatPostedDate(dateText) {
  if (!dateText) {
    return "";
  }
  // dateText looks like "2026-10-05"
  const parts = dateText.split("-");
  const year = Number(parts[0]);
  const month = Number(parts[1]) - 1;   // JavaScript counts months from 0
  const day = Number(parts[2]);
  const posted = new Date(year, month, day);

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  const daysAgo = Math.round((today - posted) / millisecondsPerDay);

  if (daysAgo <= 0) {
    return "Today";
  }
  if (daysAgo === 1) {
    return "Yesterday";
  }
  if (daysAgo < 60) {
    return daysAgo + " days ago";
  }
  const monthsAgo = Math.floor(daysAgo / 30);
  return monthsAgo + " months ago";
}

// "Berlin · 8 km"
function formatLocation(job) {
  let text = job.location;
  if (text === "") {
    text = "Location not stated";
  }
  if (job.distance_km !== null && job.distance_km !== undefined) {
    text = text + " · " + job.distance_km + " km";
  }
  return text;
}

// The top part of a card: logo square, title, company. Used on both pages.
function createJobHeader(job) {
  const top = makeElement("div", "job-top");
  top.appendChild(makeElement("div", "job-logo", getInitials(job)));

  const info = makeElement("div", "job-info");
  info.appendChild(makeElement("h3", "job-title", job.title));
  let company = job.company;
  if (company === "") {
    company = "Company not named";
  }
  info.appendChild(makeElement("p", "job-company", company));
  top.appendChild(info);
  return top;
}

// The little tags: place, job type, posted date
function createJobDetails(job) {
  const details = makeElement("ul", "job-details");
  details.appendChild(makeElement("li", "tag", formatLocation(job)));

  const typeLabel = JOB_TYPE_LABELS[job.job_type];
  if (typeLabel) {
    details.appendChild(makeElement("li", "tag", typeLabel));
  }

  const posted = formatPostedDate(job.posted_date);
  if (posted !== "") {
    let className = "tag";
    if (posted === "Today") {
      className = "tag tag-new";
    }
    details.appendChild(makeElement("li", className, "Posted " + posted.toLowerCase()));
  }
  return details;
}

// The lime "View & apply" link. It opens the job page in a new tab.
function createApplyLink(job) {
  const link = makeElement("a", "button button-lime", "View & apply");
  link.href = job.url;
  link.target = "_blank";
  // "noopener" stops the other website from controlling our tab
  link.rel = "noopener noreferrer";
  link.setAttribute("aria-label", "View and apply: " + job.title + " (opens in a new tab)");
  return link;
}

// One card in the search results
function createJobCard(job) {
  const card = makeElement("article", "job-card");
  card.appendChild(createJobHeader(job));
  card.appendChild(createJobDetails(job));

  const actions = makeElement("div", "job-actions");
  actions.appendChild(createApplyLink(job));

  const saveButton = makeElement("button", "button button-outline save-button");
  saveButton.type = "button";
  saveButton.dataset.jobId = job.id;
  updateSaveButton(saveButton);
  saveButton.addEventListener("click", function () {
    toggleSave(job, saveButton);
  });
  actions.appendChild(saveButton);

  card.appendChild(actions);
  return card;
}

// Shows "Save" or "Saved" on a button, depending on savedJobsById
function updateSaveButton(button) {
  const jobId = button.dataset.jobId;
  if (savedJobsById[jobId]) {
    button.textContent = "Saved";
    button.classList.add("is-saved");
    button.setAttribute("aria-pressed", "true");
  } else {
    button.textContent = "Save";
    button.classList.remove("is-saved");
    button.setAttribute("aria-pressed", "false");
  }
}

function refreshSaveButtons() {
  const buttons = document.querySelectorAll(".save-button");
  for (const button of buttons) {
    updateSaveButton(button);
  }
}


// =========================================================
// Saving jobs
// =========================================================

// "Save" / "Saved" button on a search result
async function toggleSave(job, button) {
  button.disabled = true;
  try {
    if (savedJobsById[job.id]) {
      await callServer("DELETE", "/api/saved/" + encodeURIComponent(job.id));
      delete savedJobsById[job.id];
    } else {
      const savedJob = await callServer("POST", "/api/saved", job);
      savedJobsById[savedJob.id] = savedJob;
    }
  } catch (error) {
    showFormMessage(error.message);
  }
  button.disabled = false;
  updateSaveButton(button);
  updateSavedCount();
}

// The lime number next to "Saved jobs" in the header
function updateSavedCount() {
  const count = Object.keys(savedJobsById).length;
  const badge = byId("saved-count");
  badge.textContent = count;
  badge.hidden = count === 0;
}

// Gets the saved jobs (and numbers) from the server and shows them
async function loadSavedJobs() {
  let savedJobs;
  let stats;
  try {
    savedJobs = await callServer("GET", "/api/saved");
    stats = await callServer("GET", "/api/stats");
  } catch (error) {
    showSavedMessage(error.message);
    return;
  }
  showSavedMessage("");

  savedJobsById = {};
  for (const savedJob of savedJobs) {
    savedJobsById[savedJob.id] = savedJob;
  }
  updateSavedCount();
  showStats(stats);
  showSavedList(savedJobs);
}

function showSavedMessage(text) {
  const message = byId("saved-message");
  message.textContent = text;
  message.hidden = text === "";
}

function showStats(stats) {
  byId("stat-saved").textContent = stats.saved;
  byId("stat-applied").textContent = stats.applied;
  byId("stat-replies").textContent = stats.replies;
  byId("stat-interviews").textContent = stats.interviews;
}

function showSavedList(savedJobs) {
  const list = byId("saved-list");
  list.replaceChildren();

  if (savedJobs.length === 0) {
    byId("saved-empty").hidden = false;
    return;
  }
  byId("saved-empty").hidden = true;

  for (const savedJob of savedJobs) {
    list.appendChild(createSavedCard(savedJob));
  }
}

// One card on the "Saved jobs" page
function createSavedCard(savedJob) {
  const card = makeElement("article", "saved-card");

  const top = createJobHeader(savedJob);
  const badge = makeElement(
    "span",
    "status-badge status-" + savedJob.status,
    STATUS_LABELS[savedJob.status]
  );
  top.appendChild(badge);
  card.appendChild(top);

  card.appendChild(createJobDetails(savedJob));

  // The status buttons: Saved, Applied, Got a reply, Interview, Rejected
  const statusRow = makeElement("div", "status-row");
  statusRow.setAttribute("role", "group");
  statusRow.setAttribute("aria-label", "Progress for " + savedJob.title);
  statusRow.appendChild(makeElement("span", "status-row-label", "Progress:"));
  for (const status of STATUS_ORDER) {
    const button = makeElement("button", "status-button", STATUS_LABELS[status]);
    button.type = "button";
    if (status === savedJob.status) {
      button.classList.add("is-current");
      button.setAttribute("aria-pressed", "true");
    } else {
      button.setAttribute("aria-pressed", "false");
    }
    button.addEventListener("click", function () {
      changeStatus(savedJob.id, status);
    });
    statusRow.appendChild(button);
  }
  card.appendChild(statusRow);

  // "View & apply" and "Remove"
  const actions = makeElement("div", "saved-actions");
  actions.appendChild(createApplyLink(savedJob));
  const removeButton = makeElement("button", "button button-outline remove-button", "Remove");
  removeButton.type = "button";
  removeButton.addEventListener("click", function () {
    removeSavedJob(savedJob.id);
  });
  actions.appendChild(removeButton);
  card.appendChild(actions);

  return card;
}

async function changeStatus(jobId, status) {
  try {
    await callServer("PUT", "/api/saved/" + encodeURIComponent(jobId) + "/status", {
      status: status,
    });
  } catch (error) {
    showSavedMessage(error.message);
    return;
  }
  // Load the list and numbers again, so everything on screen is up to date
  loadSavedJobs();
}

async function removeSavedJob(jobId) {
  try {
    await callServer("DELETE", "/api/saved/" + encodeURIComponent(jobId));
  } catch (error) {
    showSavedMessage(error.message);
    return;
  }
  loadSavedJobs();
}


// =========================================================
// Start: connect the buttons, then load what we need
// =========================================================

function setupEvents() {
  // Search box: "submit" happens when you press the button or Enter
  byId("search-form").addEventListener("submit", function (event) {
    // Stop the browser from reloading the page (that is what forms do normally)
    event.preventDefault();
    startNewSearch();
  });

  // Changing a filter searches again right away (if there was a search)
  const filterIds = ["distance-filter", "job-type-filter", "posted-filter"];
  for (const filterId of filterIds) {
    byId(filterId).addEventListener("change", function () {
      if (lastSearch !== null) {
        startNewSearch();
      }
    });
  }

  byId("clear-filters").addEventListener("click", clearFilters);
  byId("widen-search").addEventListener("click", widenSearch);
  byId("try-again").addEventListener("click", function () {
    runSearch(currentPage);
  });
  byId("show-more").addEventListener("click", function () {
    showFormMessage("");
    runSearch(currentPage + 1);
  });

  // "Popular" chips fill in the job and search
  const chips = document.querySelectorAll(".chip");
  for (const chip of chips) {
    chip.addEventListener("click", function () {
      byId("what-input").value = chip.dataset.what;
      if (byId("where-input").value.trim() === "") {
        showFormMessage("Great choice! Now tell us where you'd like to work.");
        byId("where-input").focus();
        return;
      }
      startNewSearch();
    });
  }

  // Header navigation
  byId("nav-search").addEventListener("click", function () {
    showView("search");
  });
  byId("nav-saved").addEventListener("click", function () {
    showView("saved");
  });
  byId("go-find-jobs").addEventListener("click", function () {
    showView("search");
    byId("what-input").focus();
  });
  byId("logo-link").addEventListener("click", function (event) {
    event.preventDefault();
    showView("search");
  });
}

// This runs once, when the page has loaded
async function start() {
  setupTheme();
  setupEvents();

  // Remember this before anything changes the address bar
  const startOnSavedPage = location.hash === "#saved";

  // Load saved jobs first, so search results show "Saved" correctly
  await loadSavedJobs();

  // If the address bar has a search, run it again (also when we start on the
  // saved page, so "Find jobs" still shows the results)
  loadSearchFromAddressBar();

  if (startOnSavedPage) {
    showView("saved");
  }
}

start();
