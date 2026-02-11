import http from "k6/http";
import { sleep } from "k6";

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
  let target = pages[Math.floor(Math.random() * pages.length)];
  http.get(target);
  sleep(1);
}
