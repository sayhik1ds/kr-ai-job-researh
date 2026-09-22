import {
  DETAIL_URL,
  htmlFetch,
  extractNextData,
  parseJobDetail,
  maskedTitles,
  writeError,
} from "../helpers.js"

export interface DetailOpts {
  idOrUrl: string
  format: "json" | "plain"
}

/** Accept a bare id or a /positions/<id> URL. */
export function extractId(idOrUrl: string): string | null {
  const trimmed = idOrUrl.trim()
  if (/^\d+$/.test(trimmed)) return trimmed
  const m = /\/positions\/(\d+)/.exec(trimmed)
  return m ? m[1]! : null
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const id = extractId(opts.idOrUrl)
  if (id === null) {
    writeError(`Not a GroupBy position id or /positions/<id> URL: ${opts.idOrUrl}`, "BAD_ID")
    return 2
  }
  try {
    const html = await htmlFetch(`${DETAIL_URL}/${id}`)
    if (html === "") {
      writeError(`Position ${id} not found (404) - the posting may have closed.`, "NOT_FOUND")
      return 1
    }
    const data = extractNextData(html)
    if (data === null) {
      writeError(
        `No __NEXT_DATA__ on the page for ${id} - the page structure changed.`,
        "NO_NEXT_DATA",
      )
      return 1
    }
    const job = parseJobDetail(data)
    if (job === null) {
      writeError(`Position ${id} returned an unexpected payload shape.`, "PARSE_FAILED")
      return 1
    }
    const masked = maskedTitles([job])
    if (masked.length > 0) {
      writeError(
        `Position ${id} came back masked ("${job.title}"). Refusing to emit it.`,
        "MASKED_SOURCE",
      )
      return 1
    }

    if (opts.format === "plain") {
      const lines = [
        job.title,
        `${job.company || "—"} · ${job.location || "—"} · ${job.career || "—"} · ${job.date || "—"}`,
        job.url,
        "",
      ]
      if (job.positionTypes.length) lines.push(`[직무] ${job.positionTypes.join(", ")}`)
      if (job.techStacks.length) lines.push(`[기술스택] ${job.techStacks.join(", ")}`)
      if (job.remoteWork) lines.push(`[근무형태] ${job.remoteWork}`)
      if (job.internPeriod) lines.push(`[인턴기간] ${job.internPeriod}`)
      if (job.averageReplyPeriod !== null) lines.push(`[평균 응답] ${job.averageReplyPeriod}일`)
      lines.push(
        "",
        "본문(주요업무·자격요건)은 GroupBy가 서버 렌더 데이터에 싣지 않는다. 위 URL에서 확인한다.",
      )
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
