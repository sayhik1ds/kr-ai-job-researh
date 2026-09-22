// Data source: Jumpit's public JSON API (jumpit.saramin.co.kr). No authentication.
//
//   search  https://jumpit-api.saramin.co.kr/api/positions?keyword=...
//   detail  https://jumpit-api.saramin.co.kr/api/position/{id}     <- singular "position"
//
// Note the singular/plural split: the list endpoint is /api/positions, the detail
// endpoint is /api/position/{id}. /api/positions/{id} is a 404.
//
// The api.jumpit.co.kr host answers 301 and is not the live API; jumpit-api.saramin.co.kr is.

export const SEARCH_URL = "https://jumpit-api.saramin.co.kr/api/positions"
export const DETAIL_URL = "https://jumpit-api.saramin.co.kr/api/position"
export const JOB_URL = "https://jumpit.saramin.co.kr/position"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"

const HEADERS: Record<string, string> = {
  "User-Agent": UA,
  Accept: "application/json",
  "Accept-Language": "ko-KR,ko;q=0.9",
}

/** Fetch JSON with exponential backoff on 429/5xx. Returns null on a 404. */
export async function jsonFetch(url: string): Promise<unknown | null> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      headers: HEADERS,
      redirect: "follow",
      signal: AbortSignal.timeout(15000),
    })
    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) {
        throw new Error(`Request failed: ${response.status} ${response.statusText}`)
      }
      const jitter = Math.floor(Math.random() * 500)
      await new Promise((r) => setTimeout(r, delay + jitter))
      delay = Math.min(delay * 2, 8000)
      continue
    }
    if (response.status === 404) return null
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    return response.json()
  }
  throw new Error("Request failed after max retries")
}

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  /**
   * Posting date. Null in search results: the list endpoint carries no
   * published timestamp (only `closedAt`). `detail` fills it from `publishedAt`.
   */
  date: string | null
  /** Application deadline ("상시채용" when `alwaysOpen` is set). */
  due: string | null
  /** Required years of experience, as "0~3년" or "신입". */
  career: string | null
  techStacks: string[]
  url: string
}

export interface JobDetail extends JobCard {
  responsibility: string | null
  qualifications: string | null
  preferred: string | null
  welfares: string | null
  recruitProcess: string | null
  isActive: boolean
}

function str(v: unknown): string | null {
  return typeof v === "string" && v.trim() !== "" ? v.trim() : null
}

function strList(v: unknown): string[] {
  return Array.isArray(v) ? v.map(str).filter((s): s is string => s !== null) : []
}

/** Render Jumpit's numeric min/max career pair as a human range. */
function careerRange(raw: Record<string, unknown>): string | null {
  const min = typeof raw.minCareer === "number" ? raw.minCareer : null
  const max = typeof raw.maxCareer === "number" ? raw.maxCareer : null
  if (raw.newcomer === true && min === null) return "신입"
  if (min === null && max === null) return null
  if (min !== null && max !== null) return min === max ? `${min}년` : `${min}~${max}년`
  return min !== null ? `${min}년 이상` : `~${max}년`
}

/** Normalize "2026-10-13T23:59:59" or "2026-10-13 23:59:59" down to the date. */
function dateOnly(v: unknown): string | null {
  const s = str(v)
  if (s === null) return null
  const m = /^(\d{4}-\d{2}-\d{2})/.exec(s)
  return m ? m[1]! : s
}

export function toJobCard(raw: unknown): JobCard | null {
  if (typeof raw !== "object" || raw === null) return null
  const p = raw as Record<string, unknown>
  const id = p.id
  if (typeof id !== "number" && typeof id !== "string") return null

  const locations = strList(p.locations)
  const single = str(p.location)

  return {
    id: String(id),
    title: str(p.title) ?? "",
    company: str(p.companyName),
    location: locations.length ? locations.join(", ") : single,
    date: dateOnly(p.publishedAt),
    due: p.alwaysOpen === true ? "상시채용" : dateOnly(p.closedAt),
    career: careerRange(p),
    techStacks: strList(p.techStacks),
    url: `${JOB_URL}/${id}`,
  }
}

/** Jumpit wraps list results as { result: { positions: [...] } }. */
export function parseJobCards(payload: unknown): JobCard[] {
  if (typeof payload !== "object" || payload === null) return []
  const root = payload as Record<string, unknown>
  const result = root.result
  if (typeof result !== "object" || result === null) return []
  const list = (result as Record<string, unknown>).positions
  if (!Array.isArray(list)) return []
  return list.map(toJobCard).filter((c): c is JobCard => c !== null && c.title !== "")
}

/** Total match count, for reporting how much a query matched beyond one page. */
export function parseTotalCount(payload: unknown): number | null {
  if (typeof payload !== "object" || payload === null) return null
  const result = (payload as Record<string, unknown>).result
  if (typeof result !== "object" || result === null) return null
  const total = (result as Record<string, unknown>).totalCount
  return typeof total === "number" ? total : null
}

/** Strip the HTML Jumpit embeds in its rich-text detail fields. */
function plain(v: unknown): string | null {
  const s = str(v)
  if (s === null) return null
  const text = s
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/(p|div|li)>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
  return text === "" ? null : text
}

export function parseJobDetail(payload: unknown): JobDetail | null {
  if (typeof payload !== "object" || payload === null) return null
  const root = payload as Record<string, unknown>
  const r = (root.result ?? root) as Record<string, unknown>
  const card = toJobCard(r)
  if (card === null) return null

  const closed = dateOnly(r.closedAt)
  return {
    ...card,
    responsibility: plain(r.responsibility),
    qualifications: plain(r.qualifications),
    preferred: plain(r.preferredRequirements),
    welfares: plain(r.welfares),
    recruitProcess: plain(r.recruitProcess),
    // No status flag in the payload; a past deadline is the only closure signal.
    isActive: closed === null ? true : closed >= new Date().toISOString().slice(0, 10),
  }
}
