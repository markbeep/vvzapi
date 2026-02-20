import http from "k6/http";
import { sleep } from "k6";

// Search queries using various operators and realistic course content
const searchQueries = [
  // Simple title searches
  "Water Resources",
  "Machine Learning",
  "algorithms",
  "physics",

  // Using title operator
  "t:Introduction",
  "title:Analysis",

  // Number searches
  "n:252",
  "number:401",

  // Lecturer searches
  "l:Müller",
  "lecturer:Schmidt",
  "instructor:Weber",

  // Credits filters
  "c>=4",
  "credits<=6",
  "ects=3",
  "c>6",

  // Year and semester
  "y=2025",
  "y:2024 s:W",
  "year:2026 semester:FS",
  "s:HS y=2025",

  // Department filters
  "dep:Computer Science",
  "department:Physics",
  "dept:Architecture",

  // Level filters
  "lvl:BSC",
  "level:MSC",
  "lev=DR",

  // Language filters
  "lang:English",
  "language:German",

  // Description searches
  "d:machine learning",
  "descriptions:neural networks",
  "de:optimization",

  // Offered in (section) searches
  "o:Bachelor",
  'o:"Computer Science Master"',
  'off:"Data Science"',

  // Exam type
  "e:Session",
  'examtype:"Graded Semester Performance"',

  // Course review ratings
  "cr>=4.0",
  "coursereview>3.5",

  // Negation operator
  "-physics",
  "-d:calculus",
  "algorithms -t:advanced",

  // Combined filters with AND (implicit)
  "c>=4 y:2025",
  "s:FS lvl:BSC",
  "dep:Computer t:Introduction",
  "lecturer:Müller y=2024",
  "c<=6 lang:English level:MSC",

  // Combined filters with explicit AND
  "y=2025 AND s:FS",
  "c>=3 AND c<=6",

  // OR operator
  "physics OR chemistry",
  "s:FS OR s:HS",
  "lvl:BSC OR lvl:MSC",

  // Complex queries with parentheses
  "(c>=4 o:Bachelor) OR (c>=10 dep:Architecture)",
  "s:FS y:2025 (dept:Computer c<=4 OR dept:Physics)",
  "(t:Introduction c>=3) OR (t:Advanced c>=6)",

  // Realistic complex searches from Guide examples
  'y=2026 s:fs o:"computer science master" o:minor o:"computer vision"',
  's:fs y:2026 ((dept:computer c<=4 o:"data management systems") or (dept:architecture c>=10))',
  "credits>=10",
  "lecturer:Müller year:2024",
  "physics s:W -d:analysis",

  // Multi-field searches
  "t:Project c=6",
  "n:252 y:2025",
  'l:Schmidt dept:"Computer Science"',
  "c>=6 lang:English s:FS",

  // Title searches with common course names
  "Introduction to Water Resources",
  "Research Project",
  "Renewable Energies",
  "Data Structures",
  "Linear Algebra",

  // Multiple conditions
  "y:2025 s:FS c>=4 lvl:MSC",
  "dep:Computer lang:English c<=6",
  't:"Machine Learning" y>=2024',

  // Edge cases
  "c=0",
  "y<2020",
  'te:"Advanced Topics"',
  'tg:"Einführung"',

  // Quotation marks for exact phrases
  '"Renewable Energies"',
  '"Computer Science"',
  '"Session Examination"',
];

export function setup() {
  let pages = [];
  let queue = ["http://localhost:8000/sitemap.xml"];
  let visited = new Set();

  while (queue.length > 0) {
    let url = queue.pop();
    if (visited.has(url)) continue;
    visited.add(url);

    let res = http.get(url);
    if (res.status !== 200) continue;

    let matches = res.body.match(/<loc>(.*?)<\/loc>/g) || [];
    let urls = matches.map((m) => m.replace(/<\/?loc>/g, ""));

    urls.forEach((u) => {
      if (u.endsWith(".xml")) {
        queue.push(u);
      } else {
        pages.push(u);
      }
    });
  }
  return pages;
}

export default function (pages) {
  if (!pages || pages.length === 0) return;

  // Randomly choose between visiting a page or doing a search
  if (Math.random() < 0.5) {
    // Visit a random page from sitemap
    let target = pages[Math.floor(Math.random() * pages.length)];
    http.get(target);
  } else {
    // Perform a random search query
    let query = searchQueries[Math.floor(Math.random() * searchQueries.length)];
    let encodedQuery = encodeURIComponent(query);
    http.get(`http://localhost:8000/?q=${encodedQuery}`);
  }

  sleep(1);
}
