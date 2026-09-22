import {
  LIST_URL,
  htmlFetch,
  extractNextData,
  parseJobCards,
  parseTotalCount,
  maskedTitles,
  writeError,
  type JobCard,
} from "../helpers.js"

export interface SearchOpts {
  /** Client-side filter over the fetched feed; GroupBy has no server-side search. */
  query?: string
  limit?: number
  format: "json" | "table" | "plain"
}

function matches(card: JobCard, needle: string): boolean {
  const hay = [card.title, card.company ?? "", card.positionTypes.join(" "), card.techStacks.join(" ")]
    .join(" ")
    .toLowerCase()
  return hay.includes(needle.toLowerCase())
}

function renderTable(cards: JobCard[]): string {
  if (cards.length === 0) return "No results."
  const rows = cards.map((c) => {
    const title = (c.title || "").slice(0, 40).padEnd(40)
    const company = (c.company || "—").slice(0, 18).padEnd(18)
    const career = (c.career || "—").slice(0, 10).padEnd(10)
    const types = (c.positionTypes.join(",") || "—").slice(0, 18).padEnd(18)
    return `${c.id.padEnd(7)} ${title} ${company} ${career} ${types} ${c.date || "—"}`
  })
  const header =
    "ID".padEnd(7) +
    " " +
    "TITLE".padEnd(40) +
    " " +
    "COMPANY".padEnd(18) +
    " " +
    "CAREER".padEnd(10) +
    " " +
    "ROLE".padEnd(18) +
    " DATE"
  return [header, "-".repeat(header.length), ...rows].join("\n")
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  try {
    const html = await htmlFetch(LIST_URL)
    const data = extractNextData(html)
    if (data === null) {
      writeError(
        "No __NEXT_DATA__ on groupby.kr/positions - the page structure changed. " +
          "Do not fall back to api.groupby.kr: it returns masked records.",
        "NO_NEXT_DATA",
      )
      return 1
    }

    const all = parseJobCards(data)
    const masked = maskedTitles(all)
    if (masked.length > 0) {
      writeError(
        `Masked records in the server-rendered feed (${masked.length}): ${masked[0]}. ` +
          "This should never happen from the page route; refusing to emit unreliable data.",
        "MASKED_SOURCE",
      )
      return 1
    }

    const total = parseTotalCount(data)
    let cards = opts.query ? all.filter((c) => matches(c, opts.query!)) : all
    if (opts.limit !== undefined && opts.limit >= 0) cards = cards.slice(0, opts.limit)

    if (opts.format === "table") {
      process.stdout.write(renderTable(cards) + "\n")
    } else if (opts.format === "plain") {
      process.stdout.write(
        cards
          .map(
            (c) =>
              `${c.title}\n  ${c.company || "—"} · ${c.career || "—"} · ${c.date || "—"}\n  id: ${c.id}\n  ${c.url}`,
          )
          .join("\n\n") + "\n",
      )
    } else {
      process.stdout.write(
        JSON.stringify(
          {
            meta: {
              count: cards.length,
              fetched: all.length,
              totalCount: total,
              // Surfaced so a caller never mistakes 10 rows for the whole portal.
              note: "GroupBy server-renders only the newest page of its feed; the site ignores limit/offset in the URL. Filtering is client-side over that page.",
            },
            results: cards,
          },
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
