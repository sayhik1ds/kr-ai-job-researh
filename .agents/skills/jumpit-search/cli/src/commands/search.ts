import {
  SEARCH_URL,
  jsonFetch,
  parseJobCards,
  parseTotalCount,
  writeError,
  type JobCard,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  /** Jumpit job-category ids, repeatable. 1 = 서버/백엔드 개발자. */
  jobCategories: number[]
  /** Tech-stack ids, repeatable. */
  techStacks: number[]
  /** Minimum years of experience; -1 means "not set". */
  career: number
  sort: string
  page: number
  limit?: number
  format: "json" | "table" | "plain"
}

function buildUrl(opts: SearchOpts): string {
  const params = new URLSearchParams()
  params.set("sort", opts.sort)
  params.set("page", String(opts.page))
  if (opts.query) params.set("keyword", opts.query)
  if (opts.career >= 0) params.set("career", String(opts.career))
  for (const id of opts.jobCategories) params.append("jobCategory", String(id))
  for (const id of opts.techStacks) params.append("techStack", String(id))
  return `${SEARCH_URL}?${params.toString()}`
}

function renderTable(cards: JobCard[]): string {
  if (cards.length === 0) return "No results."
  const rows = cards.map((c) => {
    const title = (c.title || "").slice(0, 40).padEnd(40)
    const company = (c.company || "—").slice(0, 20).padEnd(20)
    const loc = (c.location || "—").slice(0, 16).padEnd(16)
    const career = (c.career || "—").slice(0, 9).padEnd(9)
    return `${c.id.padEnd(9)} ${title} ${company} ${loc} ${career} ${c.due || "—"}`
  })
  const header =
    "ID".padEnd(9) +
    " " +
    "TITLE".padEnd(40) +
    " " +
    "COMPANY".padEnd(20) +
    " " +
    "LOCATION".padEnd(16) +
    " " +
    "CAREER".padEnd(9) +
    " DUE"
  return [header, "-".repeat(header.length), ...rows].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const payload = await jsonFetch(buildUrl(opts))
    const total = payload === null ? null : parseTotalCount(payload)
    let cards = payload === null ? [] : parseJobCards(payload)
    if (opts.limit !== undefined && opts.limit >= 0) cards = cards.slice(0, opts.limit)

    if (opts.format === "table") {
      process.stdout.write(renderTable(cards) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(
        cards
          .map(
            (c) =>
              `${c.title}\n  ${c.company || "—"} · ${c.location || "—"} · ${c.career || "—"} · ${c.due || "—"}\n  id: ${c.id}\n  ${c.url}`,
          )
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify(
          { meta: { count: cards.length, page: opts.page, totalCount: total }, results: cards },
          null,
          2,
        ) + "\n",
      )
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "SEARCH_FAILED")
    return 1
  }
}
