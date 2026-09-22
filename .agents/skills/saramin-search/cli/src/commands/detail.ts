import { VIEW_URL, BODY_URL, textFetch, buildDetail, writeError } from "../helpers.js"

export interface DetailOpts {
  idOrUrl: string
  format: "json" | "plain"
}

/** Accept a bare rec_idx or any saramin URL carrying rec_idx=. */
export function extractId(idOrUrl: string): string | null {
  const trimmed = idOrUrl.trim()
  if (/^\d+$/.test(trimmed)) return trimmed
  const m = /rec_idx=(\d+)/.exec(trimmed)
  return m ? m[1]! : null
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const id = extractId(opts.idOrUrl)
  if (id === null) {
    writeError(`Not a Saramin rec_idx or a URL with rec_idx=: ${opts.idOrUrl}`, "BAD_ID")
    return 2
  }
  try {
    const view = await textFetch(`${VIEW_URL}?rec_idx=${id}`)
    if (view === null) {
      writeError(`Posting ${id} not found (404) - it may have closed.`, "NOT_FOUND")
      return 1
    }
    const body = await textFetch(`${BODY_URL}?rec_idx=${id}&rec_seq=0`)
    const job = buildDetail(id, view, body)
    if (job === null) {
      writeError(`Posting ${id} returned an unexpected page shape.`, "PARSE_FAILED")
      return 1
    }
    if (opts.format === "plain") {
      const lines = [job.title, `${job.company || "—"} · ${job.career || "—"} · ${job.education || "—"} · ${job.due || "—"}`, job.url, ""]
      if (job.body) lines.push("[공고 본문]", job.body, "")
      process.stdout.write(lines.join("\n").trimEnd() + "\n")
    } else {
      process.stdout.write(JSON.stringify(job, null, 2) + "\n")
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "DETAIL_FAILED")
    return 1
  }
}
