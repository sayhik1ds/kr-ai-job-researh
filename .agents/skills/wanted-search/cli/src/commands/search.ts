import {
  SEARCH_URL,
  NAVIGATION_URL,
  jsonFetch,
  parseJobCards,
  writeError,
  type JobCard,
} from "../helpers.js"

export interface SearchOpts {
  query?: string
  /** Wanted job-group id (518 = 개발). Used when no --query is given. */
  jobGroup?: number
  /** Wanted job-category ids, e.g. 660 = 서버/백엔드 개발자. Repeatable. */
  jobIds: number[]
  /** Inclusive years-of-experience range; -1 means "not set". */
  yearsMin: number
  yearsMax: number
  location: string
  page: number
  limit?: number
  format: "json" | "table" | "plain"
}

const PAGE_SIZE = 20

function buildUrl(opts: SearchOpts): string {
  const params = new URLSearchParams()
  params.set("country", "kr")
  params.set("job_sort", "job.latest_order")
  params.set("locations", opts.location)
  params.set("limit", String(PAGE_SIZE))
  params.set("offset", String((opts.page - 1) * PAGE_SIZE))
  if (opts.yearsMin >= 0) params.append("years", String(opts.yearsMin))
  if (opts.yearsMax >= 0) params.append("years", String(opts.yearsMax))

  // Keyword search and category browse are different endpoints. `query` is only
  // honoured by search/v1; navigation/v1 silently ignores it and returns the
  // unfiltered category feed, which looks like a working search but is not.
  if (opts.query) {
    params.set("query", opts.query)
    return `${SEARCH_URL}?${params.toString()}`
  }
  if (opts.jobGroup !== undefined) params.set("job_group_id", String(opts.jobGroup))
  for (const id of opts.jobIds) params.append("job_ids", String(id))
  return `${NAVIGATION_URL}?${params.toString()}`
}

function renderTable(cards: JobCard[]): string {
  if (cards.length === 0) return "No results."
  const rows = cards.map((c) => {
    const title = (c.title || "").slice(0, 44).padEnd(44)
    const company = (c.company || "—").slice(0, 22).padEnd(22)
    const loc = (c.location || "—").slice(0, 14).padEnd(14)
    return `${c.id.padEnd(8)} ${title} ${company} ${loc} ${c.due || "—"}`
  })
  const header =
    "ID".padEnd(8) +
    " " +
    "TITLE".padEnd(44) +
    " " +
    "COMPANY".padEnd(22) +
    " " +
    "LOCATION".padEnd(14) +
    " DUE"
  return [header, "-".repeat(header.length), ...rows].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const payload = await jsonFetch(buildUrl(opts))
    let cards = payload === null ? [] : parseJobCards(payload)
    if (opts.limit !== undefined && opts.limit >= 0) cards = cards.slice(0, opts.limit)

    if (opts.format === "table") {
      process.stdout.write(renderTable(cards) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(
        cards
          .map(
            (c) =>
              `${c.title}\n  ${c.company || "—"} · ${c.location || "—"} · ${c.due || "—"}\n  id: ${c.id}\n  ${c.url}`,
          )
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify(
          { meta: { count: cards.length, page: opts.page }, results: cards },
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
