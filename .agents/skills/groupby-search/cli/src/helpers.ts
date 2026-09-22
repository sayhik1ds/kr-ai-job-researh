// Data source: GroupBy (groupby.kr), a Next.js site. We read the server-rendered
// __NEXT_DATA__ payload, NOT the api.groupby.kr JSON API.
//
// Why this matters, and why it must not be "simplified" back to the API later:
//
//   api.groupby.kr/startup-positions returns HTTP 200 with well-formed JSON for an
//   anonymous caller, so it looks like a working endpoint and passes a naive smoke
//   test. Every record it returns is masked:
//
//     GET /startup-positions/12218   ->  "[표시 제한] 머신러닝 엔지니어 (4년 이상)"
//     groupby.kr/positions/12218     ->  "백엔드 엔지니어", 피트인, 7~10년, 8 tech stacks
//
//   Same id, same record, different answer. The title, the company, the role and
//   the years are all replaced for unauthenticated API callers. A skill built on
//   that endpoint silently feeds fabricated postings into /scrape and /rank.
//   Sending Referer/Origin/Accept headers does not lift the mask; it is tied to
//   the caller, not the request shape.
//
//   The server-rendered page is the only anonymous route to real values, so that is
//   what this CLI parses.

export const LIST_URL = "https://groupby.kr/positions"
export const DETAIL_URL = "https://groupby.kr/positions"

/** Text that marks a masked record. Its presence means we read the wrong source. */
export const MASK_MARKER = "표시 제한"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"

const HEADERS: Record<string, string> = {
  "User-Agent": UA,
  Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "ko-KR,ko;q=0.9",
}

/** Fetch HTML with exponential backoff on 429/5xx. Returns "" on a 404. */
export async function htmlFetch(url: string): Promise<string> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      headers: HEADERS,
      redirect: "follow",
      signal: AbortSignal.timeout(20000),
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
    if (response.status === 404) return ""
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    return response.text()
  }
  throw new Error("Request failed after max retries")
}

const NEXT_DATA_RE =
  /<script id="__NEXT_DATA__" type="application\/json"[^>]*>([\s\S]*?)<\/script>/

/** Pull and parse the __NEXT_DATA__ blob out of a rendered page. */
export function extractNextData(html: string): unknown | null {
  const m = NEXT_DATA_RE.exec(html)
  if (m === null) return null
  try {
    return JSON.parse(m[1]!)
  } catch {
    return null
  }
}

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  /** Posting date, from `publishedAt`. */
  date: string | null
  /** GroupBy has no application deadline; kept null so the shape matches siblings. */
  due: string | null
  career: string | null
  positionTypes: string[]
  techStacks: string[]
  url: string
}

export interface JobDetail extends JobCard {
  remoteWork: string | null
  internPeriod: string | null
  averageReplyPeriod: number | null
  isActive: boolean
}

function str(v: unknown): string | null {
  return typeof v === "string" && v.trim() !== "" ? v.trim() : null
}

function dateOnly(v: unknown): string | null {
  const s = str(v)
  if (s === null) return null
  const m = /^(\d{4}-\d{2}-\d{2})/.exec(s)
  return m ? m[1]! : s
}

/** GroupBy states experience as careerType plus a {min,max} range. */
function careerRange(raw: Record<string, unknown>): string | null {
  const type = str(raw.careerType)
  const range = raw.experienceRange
  if (typeof range === "object" && range !== null) {
    const r = range as Record<string, unknown>
    const min = typeof r.min === "number" ? r.min : null
    const max = typeof r.max === "number" ? r.max : null
    if (min !== null && max !== null) {
      // min 0 with a wide max is how GroupBy encodes 신입/무관, not "0~20 years".
      if (min === 0 && max >= 20) return type ?? "경력무관"
      return min === max ? `${min}년` : `${min}~${max}년`
    }
  }
  return type
}

function nameList(v: unknown): string[] {
  if (!Array.isArray(v)) return []
  return v
    .map((t) => (typeof t === "object" && t !== null ? str((t as Record<string, unknown>).name) : str(t)))
    .filter((s): s is string => s !== null)
}

/** Company can be a nested startup object or a bare string depending on the page. */
function companyName(v: unknown): string | null {
  if (typeof v === "string") return str(v)
  if (typeof v === "object" && v !== null) return str((v as Record<string, unknown>).name)
  return null
}

export function toJobCard(raw: unknown): JobCard | null {
  if (typeof raw !== "object" || raw === null) return null
  const p = raw as Record<string, unknown>
  const id = p.id
  if (typeof id !== "number" && typeof id !== "string") return null

  return {
    id: String(id),
    title: str(p.name) ?? "",
    company: companyName(p.startup),
    location: str(p.location),
    date: dateOnly(p.publishedAt) ?? dateOnly(p.createdAt),
    due: null,
    career: careerRange(p),
    positionTypes: nameList(p.positionTypes),
    techStacks: nameList(p.techStacks),
    url: `${DETAIL_URL}/${id}`,
  }
}

/**
 * Walk the SWR fallback map on the positions page and collect the non-advertising
 * feed. Keys look like
 *   /startup-positions?isAdvertising=false&limit=10&offset=0&orderBy=-updatedAt
 */
export function parseJobCards(payload: unknown): JobCard[] {
  if (typeof payload !== "object" || payload === null) return []
  const props = (payload as Record<string, unknown>).props
  if (typeof props !== "object" || props === null) return []
  const pageProps = (props as Record<string, unknown>).pageProps
  if (typeof pageProps !== "object" || pageProps === null) return []
  const fallback = (pageProps as Record<string, unknown>).positionFallback
  if (typeof fallback !== "object" || fallback === null) return []

  const cards: JobCard[] = []
  const seen = new Set<string>()
  for (const [key, value] of Object.entries(fallback as Record<string, unknown>)) {
    // Skip the ad feed: those are sponsored placements, not the organic listing.
    if (key.includes("isAdvertising=true")) continue
    if (typeof value !== "object" || value === null) continue
    const items = (value as Record<string, unknown>).items
    if (!Array.isArray(items)) continue
    for (const item of items) {
      const card = toJobCard(item)
      if (card === null || card.title === "" || seen.has(card.id)) continue
      seen.add(card.id)
      cards.push(card)
    }
  }
  return cards
}

/** Total postings the feed reports, for context on how much the page withheld. */
export function parseTotalCount(payload: unknown): number | null {
  if (typeof payload !== "object" || payload === null) return null
  const props = (payload as Record<string, unknown>).props
  if (typeof props !== "object" || props === null) return null
  const pageProps = (props as Record<string, unknown>).pageProps
  if (typeof pageProps !== "object" || pageProps === null) return null
  const fallback = (pageProps as Record<string, unknown>).positionFallback
  if (typeof fallback !== "object" || fallback === null) return null
  for (const [key, value] of Object.entries(fallback as Record<string, unknown>)) {
    if (key.includes("isAdvertising=true")) continue
    if (typeof value !== "object" || value === null) continue
    const total = (value as Record<string, unknown>).total
    if (typeof total === "number" && total > 0) return total
  }
  return null
}

/** Find the single posting object on a detail page's props. */
function findPosting(node: unknown, depth = 0): Record<string, unknown> | null {
  if (depth > 8) return null
  if (Array.isArray(node)) {
    for (const v of node) {
      const found = findPosting(v, depth + 1)
      if (found !== null) return found
    }
    return null
  }
  if (typeof node !== "object" || node === null) return null
  const obj = node as Record<string, unknown>
  if ("name" in obj && "careerType" in obj && "id" in obj) return obj
  for (const v of Object.values(obj)) {
    const found = findPosting(v, depth + 1)
    if (found !== null) return found
  }
  return null
}

export function parseJobDetail(payload: unknown): JobDetail | null {
  if (typeof payload !== "object" || payload === null) return null
  const props = (payload as Record<string, unknown>).props
  if (typeof props !== "object" || props === null) return null
  const pageProps = (props as Record<string, unknown>).pageProps
  const posting = findPosting(pageProps)
  if (posting === null) return null

  const card = toJobCard(posting)
  if (card === null) return null

  const reply = posting.averageReplyPeriod
  return {
    ...card,
    remoteWork: str(posting.remoteWorkPreference),
    internPeriod: str(posting.internPeriod),
    averageReplyPeriod: typeof reply === "number" ? reply : null,
    // No status flag; a posting that still renders its own page is live.
    isActive: true,
  }
}

/**
 * Guard against silently reading the masked API corpus. Callers run this on
 * parsed results; a hit means the data source regressed and the output must not
 * be trusted.
 */
export function maskedTitles(cards: { title: string }[]): string[] {
  return cards.filter((c) => c.title.includes(MASK_MARKER)).map((c) => c.title)
}
