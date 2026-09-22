import {
  LIST_URL,
  LIST_REFERER,
  textFetch,
  parseJobCards,
  parseLastPage,
  writeError,
  type JobCard,
} from "../helpers.js"

export interface SearchOpts {
  /** Client-side filter (regex, case-insensitive) over title, summary and company. */
  query?: string
  /** 대분류 duty category id. Default 10031 (AI·개발·데이터). */
  dutyCtgr: string
  /** Sub-duty codes, comma-joined, passed through as condition[duty]. */
  duty?: string
  /** Region codes, comma-joined (I000 = 서울, B000 = 경기). */
  local?: string
  careerMin?: number
  careerMax?: number
  page: number
  /** Pages to fetch and merge (each page is one POST). */
  pages: number
  pageSize: number
  limit?: number
  format: "json" | "table" | "plain"
}

export function buildBody(opts: SearchOpts, page: number): string {
  const p = new URLSearchParams()
  p.set("condition[menucode]", "duty")
  p.set("condition[dutyCtgr]", opts.dutyCtgr)
  if (opts.duty) p.set("condition[duty]", opts.duty)
  if (opts.local) p.set("condition[local]", opts.local)
  if (opts.careerMin !== undefined) p.set("condition[careerStart]", String(opts.careerMin))
  if (opts.careerMax !== undefined) p.set("condition[careerEnd]", String(opts.careerMax))
  p.set("page", String(page))
  p.set("pageSize", String(opts.pageSize))
  return p.toString()
}

function renderTable(cards: JobCard[]): string {
  if (cards.length === 0) return "No results."
  const rows = cards.map((c) => {
    const title = c.title.slice(0, 40).padEnd(40)
    const company = (c.company || "—").slice(0, 20).padEnd(20)
    const loc = (c.location || "—").slice(0, 14).padEnd(14)
    const career = (c.career || "—").slice(0, 9).padEnd(9)
    return `${c.id.padEnd(9)} ${title} ${company} ${loc} ${career} ${c.due || "—"}`
  })
  const header =
    "ID".padEnd(9) + " " + "TITLE".padEnd(40) + " " + "COMPANY".padEnd(20) + " " + "LOCATION".padEnd(14) + " " + "CAREER".padEnd(9) + " DUE"
  return [header, "-".repeat(header.length), ...rows].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    let cards: JobCard[] = []
    let lastPage: number | null = null
    for (let i = 0; i < opts.pages; i++) {
      const page = opts.page + i
      const html = await textFetch(LIST_URL, { method: "POST", body: buildBody(opts, page), referer: LIST_REFERER })
      if (html === null) break
      const batch = parseJobCards(html)
      if (i === 0) lastPage = parseLastPage(html)
      cards.push(...batch)
      if (batch.length < opts.pageSize) break
    }
    const seen = new Set<string>()
    cards = cards.filter((c) => (seen.has(c.id) ? false : (seen.add(c.id), true)))
    if (opts.query) {
      const re = new RegExp(opts.query, "i")
      cards = cards.filter((c) => re.test(`${c.title} ${c.summary ?? ""} ${c.company ?? ""}`))
    }
    if (opts.limit !== undefined && opts.limit >= 0) cards = cards.slice(0, opts.limit)

    if (opts.format === "table") {
      process.stdout.write(renderTable(cards) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(
        cards
          .map((c) => `${c.title}\n  ${c.company || "—"} · ${c.location || "—"} · ${c.career || "—"} · ${c.due || "—"}\n  id: ${c.id}\n  ${c.url}`)
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify({ meta: { count: cards.length, page: opts.page, pages: opts.pages, lastPage }, results: cards }, null, 2) + "\n",
      )
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
