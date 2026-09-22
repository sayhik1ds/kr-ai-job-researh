import { SEARCH_URL, textFetch, parseJobCards, parseTotalCount, writeError, type JobCard } from "../helpers.js"

export interface SearchOpts {
  query?: string
  /** exp_cd, comma-joined: 1 신입, 2 경력, 99 경력무관. */
  expCd?: string
  expMin?: number
  expMax?: number
  /** loc_mcd, comma-joined: 101000 서울, 102000 경기. */
  loc?: string
  /** cat_kewd, comma-joined: 84 백엔드/서버개발. */
  cat?: string
  /** recruitSort: relation | reg_dt | ... passed through. */
  sort: string
  page: number
  pageSize: number
  limit?: number
  format: "json" | "table" | "plain"
}

export function buildUrl(opts: SearchOpts): string {
  const p = new URLSearchParams()
  p.set("searchType", "search")
  if (opts.query) p.set("searchword", opts.query)
  p.set("recruitPage", String(opts.page))
  p.set("recruitPageCount", String(opts.pageSize))
  p.set("recruitSort", opts.sort)
  if (opts.expCd) p.set("exp_cd", opts.expCd)
  if (opts.expMin !== undefined) p.set("exp_min", String(opts.expMin))
  if (opts.expMax !== undefined) p.set("exp_max", String(opts.expMax))
  if (opts.loc) p.set("loc_mcd", opts.loc)
  if (opts.cat) p.set("cat_kewd", opts.cat)
  return `${SEARCH_URL}?${p.toString()}`
}

function renderTable(cards: JobCard[]): string {
  if (cards.length === 0) return "No results."
  const rows = cards.map((c) => {
    const title = c.title.slice(0, 40).padEnd(40)
    const company = (c.company || "—").slice(0, 20).padEnd(20)
    const loc = (c.location || "—").slice(0, 14).padEnd(14)
    const career = (c.career || "—").slice(0, 11).padEnd(11)
    return `${c.id.padEnd(9)} ${title} ${company} ${loc} ${career} ${c.due || "—"}`
  })
  const header =
    "ID".padEnd(9) + " " + "TITLE".padEnd(40) + " " + "COMPANY".padEnd(20) + " " + "LOCATION".padEnd(14) + " " + "CAREER".padEnd(11) + " DUE"
  return [header, "-".repeat(header.length), ...rows].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const html = await textFetch(buildUrl(opts))
    const total = html === null ? null : parseTotalCount(html)
    let cards = html === null ? [] : parseJobCards(html)
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
      process.stdout.write(JSON.stringify({ meta: { count: cards.length, page: opts.page, totalCount: total }, results: cards }, null, 2) + "\n")
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
