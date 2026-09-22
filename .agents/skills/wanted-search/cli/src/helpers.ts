// Data source: Wanted's public "chaos" JSON API (wanted.co.kr). No authentication.
//
//   search    /api/chaos/search/v1/results   keyword search; jobs arrive under `positions.data`
//   navigate  /api/chaos/navigation/v1/results   category/filter browse, no keyword
//   detail    /api/chaos/jobs/v4/{id}/details
//
// Both list endpoints return the same position shape, so one parser covers them.
// The API is JSON end to end; there is no HTML to scrape.

export const SEARCH_URL = "https://www.wanted.co.kr/api/chaos/search/v1/results"
export const NAVIGATION_URL = "https://www.wanted.co.kr/api/chaos/navigation/v1/results"
export const DETAIL_URL = "https://www.wanted.co.kr/api/chaos/jobs/v4"
export const JOB_URL = "https://www.wanted.co.kr/wd"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"

/**
 * Wanted keys its response language and currency off these headers. Without them
 * the API answers in English for some fields and omits the Korean position title,
 * which is the field every downstream consumer reads.
 */
const HEADERS: Record<string, string> = {
  "User-Agent": UA,
  Accept: "application/json",
  "wanted-user-country": "KR",
  "wanted-user-language": "ko",
  "wanted-user-agent": "user-web",
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
   * Posting date, for the /scrape Step 2 contract. Always null: Wanted's list
   * endpoints expose no published/created timestamp, only `due_time`. Kept as an
   * explicit key rather than omitted so the field is visibly unavailable instead
   * of looking like a parser that dropped it. Sort order (`job.latest_order`) is
   * the only recency signal the list gives.
   */
  date: string | null
  /** Application deadline ("상시채용" when the posting has no due date). */
  due: string | null
  employmentType: string | null
  url: string
}

export interface JobDetail extends JobCard {
  intro: string | null
  mainTasks: string | null
  requirements: string | null
  preferred: string | null
  benefits: string | null
  skills: string[]
  isActive: boolean
}

function str(v: unknown): string | null {
  return typeof v === "string" && v.trim() !== "" ? v.trim() : null
}

function joinAddress(addr: unknown): string | null {
  if (typeof addr !== "object" || addr === null) return null
  const a = addr as Record<string, unknown>
  const parts = [str(a.location), str(a.district)].filter(Boolean)
  return parts.length ? parts.join(" ") : str(a.country)
}

/** Map one raw position object from either list endpoint onto a JobCard. */
export function toJobCard(raw: unknown): JobCard | null {
  if (typeof raw !== "object" || raw === null) return null
  const p = raw as Record<string, unknown>
  const id = p.id
  if (typeof id !== "number" && typeof id !== "string") return null
  const company = p.company as Record<string, unknown> | undefined
  return {
    id: String(id),
    // Wanted pads many titles with a trailing space; trim so dedup keys stay stable.
    title: str(p.position) ?? "",
    company: company ? str(company.name) : null,
    location: joinAddress(p.address),
    date: null,
    due: str(p.due_time) ?? "상시채용",
    employmentType: str(p.employment_type),
    url: `${JOB_URL}/${id}`,
  }
}

/**
 * Pull the positions array out of a list response. The search endpoint nests jobs
 * under `positions.data` alongside companies/careers/social_posts; the navigation
 * endpoint returns them at the top level under `data`.
 */
export function parseJobCards(payload: unknown): JobCard[] {
  if (typeof payload !== "object" || payload === null) return []
  const root = payload as Record<string, unknown>
  let list: unknown = null

  const positions = root.positions
  if (typeof positions === "object" && positions !== null) {
    const inner = (positions as Record<string, unknown>).data
    if (Array.isArray(inner)) list = inner
  }
  if (list === null && Array.isArray(root.data)) list = root.data
  if (!Array.isArray(list)) return []

  return list.map(toJobCard).filter((c): c is JobCard => c !== null && c.title !== "")
}

/** Strip HTML tags from Wanted's rich-text detail fields. */
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
  const data = (root.data ?? root) as Record<string, unknown>
  const job = (data.job ?? data) as Record<string, unknown>
  const detail = (job.detail ?? {}) as Record<string, unknown>

  // The detail endpoint puts the job title on `detail.position`, not on the job
  // object itself (the list endpoints put it on `position`). `job.name` is null
  // here, so reading the card fields off `job` alone yields an empty title.
  const card = toJobCard({
    id: job.id,
    position: detail.position ?? job.name,
    company: job.company,
    address: job.address,
    due_time: job.due_time,
    employment_type: job.employment_type,
  })
  if (card === null) return null

  const skillsRaw = job.skill_tags
  const skills = Array.isArray(skillsRaw)
    ? skillsRaw
        .map((t) =>
          typeof t === "object" && t !== null
            ? // Skill tags carry the label on `text`; `title` does not exist here.
              (str((t as Record<string, unknown>).text) ??
              str((t as Record<string, unknown>).title))
            : str(t),
        )
        .filter((s): s is string => s !== null)
    : []

  return {
    ...card,
    intro: plain(detail.intro),
    mainTasks: plain(detail.main_tasks),
    requirements: plain(detail.requirements),
    preferred: plain(detail.preferred_points),
    benefits: plain(detail.benefits),
    skills,
    isActive: job.status === undefined ? true : job.status === "active",
  }
}
