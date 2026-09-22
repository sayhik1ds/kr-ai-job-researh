import { describe, expect, test } from "bun:test"
import { parseJobCards, parseLastPage, buildDetail, stripTags } from "../src/helpers.ts"
import { extractId } from "../src/commands/detail.ts"
import { buildBody } from "../src/commands/search.ts"

const ROW = `
<table><tr class="devloopArea" data-gno="50038259" data-index="0">
<td class="tplCo"><a href="/Recruit/Co_Read/C/1" class="link normalLog">㈜큐센텍</a></td>
<td class="tplTit"><div class="titBx">
<strong><a href="/Recruit/GI_Read/50038259?rPageCode=PL" class="link normalLog" title="[경력] JAVA 기반 백엔드 개발자">[경력] JAVA 기반 백엔드 개발자</a></strong>
<p class="etc"><span class="cell">경력3년↑</span><span class="cell">대졸↑</span><span class="cell">서울 영등포구</span><span class="cell">4,000~5,000만원</span><span class="cell">주임~대리급 외</span><span class="cell">정규직</span></p>
<p class="dsc">시스템 연계 &amp; 도메인 API</p></div></td>
<td class="odd"><span class="time dotum"><span class="tahoma">4</span>분 전 등록</span><span class="date dotum"><span class="tahoma">~10/22</span>(목)</span></td>
</tr></table>
<div class="tplPagination"><ul><li><span class="now" data-page="1">1</span></li><li><a data-page="2">2</a></li><li><a data-page="11">11</a></li></ul></div>
`

describe("parseJobCards", () => {
  test("classifies cells", () => {
    const [c] = parseJobCards(ROW)
    expect(c).toBeDefined()
    expect(c!.id).toBe("50038259")
    expect(c!.title).toBe("[경력] JAVA 기반 백엔드 개발자")
    expect(c!.company).toBe("㈜큐센텍")
    expect(c!.career).toBe("경력3년↑")
    expect(c!.education).toBe("대졸↑")
    expect(c!.location).toBe("서울 영등포구")
    expect(c!.salary).toBe("4,000~5,000만원")
    expect(c!.level).toBe("주임~대리급 외")
    expect(c!.employmentType).toBe("정규직")
    expect(c!.summary).toBe("시스템 연계 & 도메인 API")
    expect(c!.date).toBe("4 분 전 등록")
    expect(c!.due).toBe("~10/22")
    expect(c!.url).toBe("https://www.jobkorea.co.kr/Recruit/GI_Read/50038259")
  })
  test("last page", () => {
    expect(parseLastPage(ROW)).toBe(11)
    expect(parseLastPage("<p>none</p>")).toBeNull()
  })
})

describe("buildDetail", () => {
  const PAGE = `<html><head><meta property="og:title" content="큐센텍 채용 - 백엔드 | 잡코리아">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"JobPosting","title":"백엔드 개발자","datePosted":"2026-09-18","validThrough":"2026-10-22T23:59","employmentType":"FULL_TIME","experienceRequirements":"경력","educationRequirements":"대졸 이상","hiringOrganization":{"@type":"Organization","name":"㈜큐센텍"},"jobLocation":{"@type":"Place","address":{"@type":"PostalAddress","streetAddress":"서울 영등포구 양평동3가 67-16"}}}</script></head></html>`
  test("reads ld+json and body", () => {
    const d = buildDetail("50038259", PAGE, "<div><p>주요업무</p><ul><li>API 개발</li></ul></div>")
    expect(d).not.toBeNull()
    expect(d!.title).toBe("백엔드 개발자")
    expect(d!.company).toBe("㈜큐센텍")
    expect(d!.due).toBe("2026-10-22")
    expect(d!.date).toBe("2026-09-18")
    expect(d!.location).toBe("서울 영등포구")
    expect(d!.address).toBe("서울 영등포구 양평동3가 67-16")
    expect(d!.body).toBe("주요업무\nAPI 개발")
  })
  test("falls back to og:title", () => {
    const d = buildDetail("1", `<meta property="og:title" content="회사 채용 - 제목 | 잡코리아">`, null)
    expect(d!.title).toBe("회사 채용 - 제목")
    expect(d!.body).toBeNull()
    expect(d!.isActive).toBe(true)
  })
})

describe("cli helpers", () => {
  test("extractId", () => {
    expect(extractId("50038259")).toBe("50038259")
    expect(extractId("https://www.jobkorea.co.kr/Recruit/GI_Read/50038259?rPageCode=PL")).toBe("50038259")
    expect(extractId("https://www.jobkorea.co.kr/")).toBeNull()
  })
  test("buildBody uses bracket encoding", () => {
    const body = buildBody({ dutyCtgr: "10031", local: "I000", careerMin: 0, careerMax: 3, page: 1, pages: 1, pageSize: 40, format: "json" }, 2)
    expect(body).toContain("condition%5BdutyCtgr%5D=10031")
    expect(body).toContain("condition%5Blocal%5D=I000")
    expect(body).toContain("condition%5BcareerStart%5D=0")
    expect(body).toContain("condition%5BcareerEnd%5D=3")
    expect(body).toContain("page=2")
  })
  test("stripTags collapses whitespace", () => {
    expect(stripTags("<p>a&nbsp;b</p>\n\n\n<p>c</p>")).toBe("a b\n\nc")
  })
})
