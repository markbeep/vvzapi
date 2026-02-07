const searchbar = document.getElementById("search-bar");
const queries = [
  'e:"Graded Semester Performance" semester:fs level:MSC y:2026 c>3',
  "big data",
  'dep:math c>5 e:"Session Examination"',
  'dept:infk o:"interfocus"',
  "lecturer:krause",
  'y=2026 s:fs o:minor o:"computer vision"',
];

let inactivityTimer = null;
let typingInterval = null;
let deletingInterval = null;
let displayTimeout = null;
let currentQuery = "";
let currentIndex = 0;

// times in ms
const INACTIVITY_DELAY = 5000;
const TYPING_SPEED = 50;
const DELETING_SPEED = 20;
const BASE_DISPLAY_TIME = 3000;
const CHAR_DISPLAY_TIME = 30;

function clearAllTimers() {
  if (inactivityTimer) clearTimeout(inactivityTimer);
  if (typingInterval) clearInterval(typingInterval);
  if (deletingInterval) clearInterval(deletingInterval);
  if (displayTimeout) clearTimeout(displayTimeout);
  inactivityTimer = null;
  typingInterval = null;
  deletingInterval = null;
  displayTimeout = null;
}

function typeQuery() {
  currentQuery = queries[Math.floor(Math.random() * queries.length)];
  currentIndex = 0;

  typingInterval = setInterval(() => {
    if (currentIndex < currentQuery.length) {
      searchbar.placeholder = currentQuery.substring(0, currentIndex + 1);
      currentIndex++;
    } else {
      clearInterval(typingInterval);
      typingInterval = null;

      // Calculate display time based on query length
      const displayTime =
        BASE_DISPLAY_TIME + currentQuery.length * CHAR_DISPLAY_TIME;

      displayTimeout = setTimeout(() => {
        deleteQuery();
      }, displayTime);
    }
  }, TYPING_SPEED);
}

function deleteQuery() {
  deletingInterval = setInterval(() => {
    if (currentIndex > 0) {
      currentIndex--;
      searchbar.placeholder = currentQuery.substring(0, currentIndex);
    } else {
      clearInterval(deletingInterval);
      deletingInterval = null;
      searchbar.placeholder = "";
      // Restart the inactivity timer
      startInactivityTimer();
    }
  }, DELETING_SPEED);
}

function startInactivityTimer() {
  clearAllTimers();
  inactivityTimer = setTimeout(() => {
    if (!searchbar.value) {
      typeQuery();
    }
  }, INACTIVITY_DELAY);
}

function resetAnimation() {
  clearAllTimers();
  searchbar.placeholder = "";
  currentIndex = 0;
  currentQuery = "";

  // Only restart timer if input is empty
  if (!searchbar.value) {
    startInactivityTimer();
  }
}

searchbar.addEventListener("input", resetAnimation);
searchbar.addEventListener("focus", resetAnimation);

startInactivityTimer();
