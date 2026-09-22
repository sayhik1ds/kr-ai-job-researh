import { DETAIL_URL, jsonFetch, parseJobDetail, writeError } from "../helpers.js"

export interface DetailOpts {
  idOrUrl: string
  format: "json" | "plain"
}

/** Accept a bare id, a /wd/<id> URL, or a full posting URL with query string. */
export function extractId(idOrUrl: string): string | null {
  const trimmed = idOrUrl.trim()
  if (/^\d+$/.test(trimmed)) return trimmed
  const m = /\/wd\/(\d+)/.exec(trimmed)
  return m ? m[1]! : null
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const id = extractId(opts.idOrUrl)
  if (id === null) {
    writeError(`Not a Wanted job id or /wd/<id> URL: ${opts.idOrUrl}`, "BAD_ID")
    return 2
  }
  try {
    const payload = await jsonFetch(`${DETAIL_URL}/${id}/details`)
    if (payload === null) {
      writeError(`Job ${id} not found (404) - the posting may have closed.`, "NOT_FOUND")
      return 1
    }
    const job = parseJobDetail(payload)
    if (job === null) {
      writeError(`Job ${id} returned an unexpected payload shape.`, "PARSE_FAILED")
      return 1
    }

    if (opts.format === "plain") {
      const lines = [
        job.title,
        `${job.company || "—"} · ${job.location || "—"} · ${job.due || "—"}`,
        job.url,
        "",
      ]
      if (job.skills.length) lines.push(`[스킬] ${job.skills.join(", ")}`, "")
      if (job.intro) lines.push("[회사소개]", job.intro, "")
      if (job.mainTasks) lines.push("[주요업무]", job.mainTasks, "")
      if (job.requirements) lines.push("[자격요건]", job.requirements, "")
      if (job.preferred) lines.push("[우대사항]", job.preferred, "")
      if (job.benefits) lines.push("[혜택 및 복지]", job.benefits, "")
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
