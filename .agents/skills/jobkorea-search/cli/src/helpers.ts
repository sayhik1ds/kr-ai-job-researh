// Data source: JobKorea's logged-out web pages (jobkorea.co.kr). No authentication.
//
//   list    POST https://www.jobkorea.co.kr/Recruit/Home/_GI_List/   (HTML fragment)
//   detail  GET  https://www.jobkorea.co.kr/Recruit/GI_Read/{id}      (ld+json JobPosting)
//   body    GET  https://www.jobkorea.co.kr/Recruit/GI_Read_Comt_Ifrm?Gno={id}
//
// robots.txt disallows /Search/?stext= for every user agent, so there is no
// keyword-search endpoint here. Keyword filtering happens client-side over the
// category list. /recruit/joblist and /Recruit/GI_Read are allowed.

export const LIST_URL = "https://www.jobkorea.co.kr/Recruit/Home/_GI_List/"
export const DETAIL_URL = "https://www.jobkorea.co.kr/Recruit/GI_Read"
export const BODY_URL = "https://www.jobkorea.co.kr/Recruit/GI_Read_Comt_Ifrm?Gno="
export const LIST_REFERER = "https://www.jobkorea.co.kr/recruit/joblist?menucode=duty"

/** Top-level duty category ids (대분류). Sub-duty codes are loaded lazily by the site and not enumerated here. */
export const DUTY_CTGR: Record<string, string> = {
  "10031": "AI·개발·데이터",
  "10040": "엔지니어링·설계",
  "10026": "기획·전략",
  "10032": "디자인",
  "10030": "마케팅·광고·MD",
}

/** Region codes (시/도). Districts are not enumerated. */
export const LOCAL: Record<string, string> = {
  I000: "서울특별시",
  B000: "경기도",
  K000: "인천광역시",
  H000: "부산광역시",
  J000: "대전광역시",
  F000: "대구광역시",
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"

const HEADERS: Record<string, string> = {
  "User-Agent": UA,
  Accept: "text/html,application/xhtml+xml",
  "Accept-Language": "ko-KR,ko;q=0.9",
}

/** Fetch text with exponential backoff on 429/5xx. Returns null on a 404. */
export async function textFetch(
  url: string,
  init: { method?: "GET" | "POST"; body?: string; referer?: string } = {},
): Promise<string | null> {
  const maxRetries = 6
  let delay = 500
  const headers: Record<string, string> = { ...HEADERS }
  if (init.referer) headers.Referer = init.referer
  if (init.method === "POST") {
    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    headers["X-Requested-With"] = "XMLHttpRequest"
  }
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, {
      method: init.method ?? "GET",
      headers,
      body: init.body,
      redirect: "follow",
      signal: AbortSignal.timeout(20000),
    })
    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) throw new Error(`Request failed: ${response.status} ${response.statusText}`)
      const jitter = Math.floor(Math.random() * 500)
      await new Promise((r) => setTimeout(r, delay + jitter))
      delay = Math.min(delay * 2, 8000)
      continue
    }
    if (response.status === 404) return null
    if (!response.ok) throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    return response.text()
  }
  throw new Error("Request failed after max retries")
}

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  /** Registration hint as shown in the list ("4분 전 등록", "09/21 등록"). Null in detail unless ld+json has datePosted. */
  date: string | null
  /** Deadline as shown ("~10/31" in the list, ISO date in detail). */
  due: string | null
  /** "경력3년↑", "신입", "경력무관", "신입·경력" as shown. */
  career: string | null
  education: string | null
  employmentType: string | null
  /** "4,000~5,000만원", "500~850만원(월)" when shown. */
  salary: string | null
  /** "주임~대리급" and similar position hints when shown. */
  level: string | null
  /** One-line summary under the title, when present. */
  summary: string | null
  url: string
}

export interface JobDetail extends JobCard {
  address: string | null
  body: string | null
  isActive: boolean
}

export function decode(s: string): string {
  return s
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&#x27;/g, "'")
    .replace(/&#183;|&middot;/g, "·")
    .replace(/&#(\d+);/g, (_, n: string) => String.fromCodePoint(Number(n)))
}

export function stripTags(s: string): string {
  return decode(
    s
      .replace(/<(script|style)[^>]*>[\s\S]*?<\/\1>/gi, "")
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/(p|div|li|tr|h\d|dt|dd|section|table)>/gi, "\n")
      .replace(/<[^>]+>/g, " "),
  )
    .split("\n")
    .map((l) => l.replace(/[ \t ]+/g, " ").trim())
    .filter((l, i, arr) => l !== "" || (i > 0 && arr[i - 1] !== ""))
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
}

function text(s: string | undefined): string | null {
  if (s === undefined) return null
  const t = stripTags(s).replace(/\s+/g, " ").trim()
  return t === "" ? null : t
}

const CAREER_RE = /^(경력|신입|경력무관|신입·경력|신입\/경력)/
const EDU_RE = /^(학력무관|고졸|초대졸|대졸|석사|박사|대학|초대학)/
const EMPLOY_RE = /(정규직|계약직|인턴|파견직|프리랜서|위촉직|병역특례|아르바이트|기간제)/
const SALARY_RE = /(만원|원\(월\)|연봉|월급|시급|회사내규)/
const LEVEL_RE = /(사원|주임|대리|과장|차장|부장|팀원|팀장|매니저|리드|급\b|급 외|급$)/

/** Parse the HTML fragment returned by _GI_List into cards. */
export function parseJobCards(html: string): JobCard[] {
  const cards: JobCard[] = []
  const rowRe = /<tr class=" ?devloopArea"[^>]*data-gno="(\d+)"[^>]*>([\s\S]*?)<\/tr>/g
  let m: RegExpExecArray | null
  while ((m = rowRe.exec(html)) !== null) {
    const id = m[1]!
    const row = m[2]!
    const title = text(/<td class="tplTit">[\s\S]*?<strong><a[^>]*>([\s\S]*?)<\/a>/.exec(row)?.[1]) ?? ""
    const company = text(/<td class="tplCo">[\s\S]*?<a[^>]*class="link[^"]*"[^>]*>([\s\S]*?)<\/a>/.exec(row)?.[1])
    const cells = [...row.matchAll(/<span class="cell">([\s\S]*?)<\/span>/g)]
      .map((c) => text(c[1]))
      .filter((c): c is string => c !== null)
    let career: string | null = null
    let education: string | null = null
    let employmentType: string | null = null
    let salary: string | null = null
    let level: string | null = null
    const locs: string[] = []
    for (const c of cells) {
      if (career === null && CAREER_RE.test(c)) career = c
      else if (education === null && EDU_RE.test(c)) education = c
      else if (employmentType === null && EMPLOY_RE.test(c)) employmentType = c
      else if (salary === null && SALARY_RE.test(c)) salary = c
      else if (level === null && LEVEL_RE.test(c)) level = c
      else locs.push(c)
    }
    const summary = text(/<p class="dsc">([\s\S]*?)<\/p>/.exec(row)?.[1])
    const date = text(/<span class="time dotum">([\s\S]*?)<\/span>\s*<span class="date/.exec(row)?.[1])
    const due = text(/<span class="date dotum">([\s\S]*?)<\/span>/.exec(row)?.[1])
    if (title === "") continue
    cards.push({
      id,
      title,
      company,
      location: locs.length ? locs.join(", ") : null,
      date,
      due,
      career,
      education,
      employmentType,
      salary,
      level,
      summary,
      url: `${DETAIL_URL}/${id}`,
    })
  }
  return cards
}

/** Highest page number present in the fragment's pagination, or null. */
export function parseLastPage(html: string): number | null {
  const pages = [...html.matchAll(/data-page="(\d+)"/g)].map((x) => Number(x[1]))
  return pages.length ? Math.max(...pages) : null
}

interface LdJobPosting {
  title?: string
  description?: string
  datePosted?: string
  validThrough?: string
  employmentType?: string
  experienceRequirements?: string
  educationRequirements?: string
  hiringOrganization?: { name?: string }
  jobLocation?: { address?: { streetAddress?: string; addressLocality?: string } }
}

export function parseLdJobPosting(html: string): LdJobPosting | null {
  const re = /<script type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g
  let m: RegExpExecArray | null
  while ((m = re.exec(html)) !== null) {
    try {
      const j = JSON.parse(m[1]!) as Record<string, unknown>
      if (j["@type"] === "JobPosting") return j as LdJobPosting
    } catch {
      /* try next block */
    }
  }
  return null
}

function dateOnly(v: string | undefined): string | null {
  if (!v) return null
  const m = /^(\d{4}-\d{2}-\d{2})/.exec(v)
  return m ? m[1]! : v
}

export function buildDetail(id: string, pageHtml: string, bodyHtml: string | null): JobDetail | null {
  const ld = parseLdJobPosting(pageHtml)
  const ogTitle = /property="og:title" content="([^"]*)"/.exec(pageHtml)?.[1]
  const title = ld?.title ?? (ogTitle ? decode(ogTitle).replace(/\s*\|\s*잡코리아\s*$/, "") : null)
  if (!title) return null
  const address = ld?.jobLocation?.address?.streetAddress ?? null
  const due = dateOnly(ld?.validThrough)
  return {
    id,
    title,
    company: ld?.hiringOrganization?.name ?? null,
    location: address ? address.split(" ").slice(0, 2).join(" ") : null,
    date: dateOnly(ld?.datePosted),
    due,
    career: ld?.experienceRequirements ?? null,
    education: ld?.educationRequirements ?? null,
    employmentType: ld?.employmentType ?? null,
    salary: null,
    level: null,
    summary: ld?.description ?? null,
    url: `${DETAIL_URL}/${id}`,
    address,
    body: bodyHtml ? stripTags(bodyHtml) || null : null,
    isActive: due === null ? true : due >= new Date().toISOString().slice(0, 10),
  }
}
