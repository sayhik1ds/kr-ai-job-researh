import { DETAIL_URL, BODY_URL, textFetch, buildDetail, writeError } from "../helpers.js"

export interface DetailOpts {
  idOrUrl: string
  format: "json" | "plain"
}

/** Accept a bare id or a /Recruit/GI_Read/<id> URL. */
export function extractId(idOrUrl: string): string | null {
  const trimmed = idOrUrl.trim()
  if (/^\d+$/.test(trimmed)) return trimmed
  const m = /GI_Read\/(\d+)/i.exec(trimmed)
  return m ? m[1]! : null
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const id = extractId(opts.idOrUrl)
  if (id === null) {
    writeError(`Not a JobKorea posting id or /Recruit/GI_Read/<id> URL: ${opts.idOrUrl}`, "BAD_ID")
    return 2
  }
  try {
    const page = await textFetch(`${DETAIL_URL}/${id}`)
    if (page === null) {
      writeError(`Posting ${id} not found (404) - it may have closed.`, "NOT_FOUND")
      return 1
    }
    const body = await textFetch(`${BODY_URL}${id}`)
    const job = buildDetail(id, page, body)
    if (job === null) {
      writeError(`Posting ${id} returned an unexpected page shape.`, "PARSE_FAILED")
      return 1
    }
    if (opts.format === "plain") {
      const lines = [
        job.title,
        `${job.company || "—"} · ${job.address || job.location || "—"} · ${job.career || "—"} · ${job.due || "—"}`,
        job.url,
        "",
      ]
      if (job.summary) lines.push(job.summary, "")
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
