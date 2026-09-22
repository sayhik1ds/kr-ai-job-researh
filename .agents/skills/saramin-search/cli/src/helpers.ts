// Data source: Saramin's logged-out web pages (saramin.co.kr). No authentication.
//
//   search  GET https://www.saramin.co.kr/zf_user/search/recruit?searchType=search&searchword=...
//   detail  GET https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx={id}        (og: meta summary)
//   body    GET https://www.saramin.co.kr/zf_user/jobs/relay/view-detail?rec_idx={id}&rec_seq=0
//
// robots.txt allows /zf_user/search/recruit and /zf_user/jobs/... for "*". It blocks
// GPTBot and Bytespider outright, so treat this as personal-use tooling and keep
// volume low. Saramin also runs an official Open API (oapi.saramin.co.kr) that
// needs an access key; that is the sanctioned route for anything heavier.

export const SEARCH_URL = "https://www.saramin.co.kr/zf_user/search/recruit"
export const VIEW_URL = "https://www.saramin.co.kr/zf_user/jobs/relay/view"
export const BODY_URL = "https://www.saramin.co.kr/zf_user/jobs/relay/view-detail"
export const JOB_URL = "https://www.saramin.co.kr/zf_user/jobs/view"

/** exp_cd values. */
export const EXP_CD: Record<string, string> = { "1": "신입", "2": "경력", "99": "경력무관" }
/** loc_mcd values (시/도). */
export const LOC_MCD: Record<string, string> = {
  "101000": "서울",
  "102000": "경기",
  "108000": "인천",
  "106000": "부산",
  "105000": "대전",
  "104000": "대구",
}
/** cat_kewd examples (직무 키워드 카테고리). */
export const CAT_KEWD: Record<string, string> = {
  "84": "백엔드/서버개발",
  "235": "Java",
  "272": "Python",
  "92": "프론트엔드",
  "87": "데이터엔지니어",
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
export async function textFetch(url: string): Promise<string | null> {
  const maxRetries = 6
  let delay = 500
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, { headers: HEADERS, redirect: "follow", signal: AbortSignal.timeout(20000) })
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
  /** Registration or modification date as shown ("수정일 26/09/21"). */
  date: string | null
  /** Deadline as shown ("~ 10/25(일)", "상시채용", "채용시"). */
  due: string | null
  /** "경력 5~10년", "신입", "경력무관" as shown. */
  career: string | null
  education: string | null
  employmentType: string | null
  salary: string | null
  /** Job sector keywords shown under the title. */
  sectors: string[]
  url: string
}

export interface JobDetail extends JobCard {
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

const CAREER_RE = /^(경력|신입)/
const EDU_RE = /(학력무관|고졸|초대졸|대졸|석사|박사|대학원)/
const EMPLOY_RE = /(정규직|계약직|인턴|파견직|프리랜서|위촉직|병역특례|아르바이트|기간제|전문연구요원)/
const SALARY_RE = /(만원|원\)|연봉|월급|시급)/

/** Parse a search result page into cards. */
export function parseJobCards(html: string): JobCard[] {
  const cards: JobCard[] = []
  const parts = html.split(/<div class="item_recruit" value="/)
  for (const part of parts.slice(1)) {
    const id = /^(\d+)/.exec(part)?.[1]
    if (!id) continue
    const block = part.split(/<div class="item_recruit"/)[0]!
    const titleA = /<h2 class="job_tit">\s*<a[^>]*title="([^"]*)"/.exec(block)?.[1]
    const title = titleA ? decode(titleA).trim() : (text(/<h2 class="job_tit">([\s\S]*?)<\/h2>/.exec(block)?.[1]) ?? "")
    if (title === "") continue
    const corpA = /<strong class="corp_name">\s*<a[^>]*title="([^"]*)"/.exec(block)?.[1]
    const company = corpA ? decode(corpA).trim() : text(/<strong class="corp_name">([\s\S]*?)<\/strong>/.exec(block)?.[1])
    const condHtml = /<div class="job_condition">([\s\S]*?)<\/div>/.exec(block)?.[1] ?? ""
    const cells = [...condHtml.matchAll(/<span>([\s\S]*?)<\/span>/g)].map((c) => text(c[1])).filter((c): c is string => c !== null)
    let career: string | null = null
    let education: string | null = null
    let employmentType: string | null = null
    let salary: string | null = null
    const locs: string[] = []
    for (const c of cells) {
      if (career === null && CAREER_RE.test(c)) career = c
      else if (education === null && EDU_RE.test(c)) education = c
      else if (employmentType === null && EMPLOY_RE.test(c)) employmentType = c
      else if (salary === null && SALARY_RE.test(c)) salary = c
      else locs.push(c.replace(/\s*,\s*/g, ", "))
    }
    const sectorHtml = /<div class="job_sector">([\s\S]*?)<\/div>/.exec(block)?.[1] ?? ""
    const sectors = [...sectorHtml.matchAll(/<a[^>]*>([\s\S]*?)<\/a>/g)].map((a) => text(a[1])).filter((s): s is string => s !== null)
    const date = text(/<span class="job_day">([\s\S]*?)<\/span>/.exec(block)?.[1])
    const due = text(/<span class="date">([\s\S]*?)<\/span>/.exec(block)?.[1])
    cards.push({
      id,
      title,
      company,
      location: locs.length ? locs.join(" ") : null,
      date,
      due,
      career,
      education,
      employmentType,
      salary,
      sectors,
      url: `${JOB_URL}?rec_idx=${id}`,
    })
  }
  return cards
}

/** "총 2,638건" from the result page, or null. */
export function parseTotalCount(html: string): number | null {
  const m = /class="cnt_result">\s*총\s*([\d,]+)\s*건/.exec(html)
  return m ? Number(m[1]!.replace(/,/g, "")) : null
}

function dateFromDue(due: string | null): string | null {
  if (!due) return null
  const m = /(\d{4}-\d{2}-\d{2})/.exec(due)
  return m ? m[1]! : null
}

/** Build a detail from the view page's og: meta and the body endpoint's HTML. */
export function buildDetail(id: string, viewHtml: string, bodyHtml: string | null): JobDetail | null {
  const ogTitle = /property="og:title" content="([^"]*)"/.exec(viewHtml)?.[1]
  const ogDesc = /property="og:description" content="([^"]*)"/.exec(viewHtml)?.[1]
  if (!ogTitle) return null
  // og:title = "[회사] 제목(D-33) - 사람인"
  const t = decode(ogTitle).replace(/\s*-\s*사람인\s*$/, "")
  const companyM = /^\[([^\]]+)\]\s*/.exec(t)
  const company = companyM ? companyM[1]!.trim() : null
  const title = t.replace(/^\[[^\]]+\]\s*/, "").replace(/\((D-\d+|마감|상시채용|채용시)\)\s*$/, "").trim()
  // og:description = "회사, 제목, 경력:경력 5~10년, 학력:대학졸업(2,3년)이상, 면접 후 결정, 마감일:2026-10-25, 홈페이지:..."
  const desc = ogDesc ? decode(ogDesc) : ""
  // Values may themselves contain commas ("대학졸업(2,3년)이상"), so stop only before the next known key.
  const field = (k: string): string | null => {
    const m = new RegExp(`${k}:(.*?)(?=,\\s*(?:경력|학력|급여|마감일|홈페이지):|$)`).exec(desc)
    if (!m) return null
    // Unkeyed trailing items ("면접 후 결정") follow a comma that is not part of a number.
    return m[1]!.split(/,\s(?!\d)/)[0]!.trim()
  }
  const due = field("마감일")
  const body = bodyHtml ? stripTags(bodyHtml).replace(/^채용공고 상세\n?/, "") || null : null
  return {
    id,
    title,
    company,
    location: null,
    date: null,
    due,
    career: field("경력"),
    education: field("학력"),
    employmentType: null,
    salary: null,
    sectors: [],
    url: `${JOB_URL}?rec_idx=${id}`,
    body,
    isActive: (() => {
      const d = dateFromDue(due)
      return d === null ? true : d >= new Date().toISOString().slice(0, 10)
    })(),
  }
}
