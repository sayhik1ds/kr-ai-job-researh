import { DETAIL_URL, jsonFetch, parseJobDetail, writeError } from "../helpers.js"

export interface DetailOpts {
  idOrUrl: string
  format: "json" | "plain"
}

/** Accept a bare id or a /position/<id> URL. */
export function extractId(idOrUrl: string): string | null {
  const trimmed = idOrUrl.trim()
  if (/^\d+$/.test(trimmed)) return trimmed
  const m = /\/position\/(\d+)/.exec(trimmed)
  return m ? m[1]! : null
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const id = extractId(opts.idOrUrl)
  if (id === null) {
    writeError(`Not a Jumpit position id or /position/<id> URL: ${opts.idOrUrl}`, "BAD_ID")
    return 2
  }
  try {
    const payload = await jsonFetch(`${DETAIL_URL}/${id}`)
    if (payload === null) {
      writeError(`Position ${id} not found (404) - the posting may have closed.`, "NOT_FOUND")
      return 1
    }
    const job = parseJobDetail(payload)
    if (job === null) {
      writeError(`Position ${id} returned an unexpected payload shape.`, "PARSE_FAILED")
      return 1
    }

    if (opts.format === "plain") {
      const lines = [
        job.title,
        `${job.company || "—"} · ${job.location || "—"} · ${job.career || "—"} · ${job.due || "—"}`,
        job.url,
        "",
      ]
      if (job.techStacks.length) lines.push(`[기술스택] ${job.techStacks.join(", ")}`, "")
      if (job.responsibility) lines.push("[주요업무]", job.responsibility, "")
      if (job.qualifications) lines.push("[자격요건]", job.qualifications, "")
      if (job.preferred) lines.push("[우대사항]", job.preferred, "")
      if (job.recruitProcess) lines.push("[채용절차]", job.recruitProcess, "")
      if (job.welfares) lines.push("[복지]", job.welfares, "")
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
