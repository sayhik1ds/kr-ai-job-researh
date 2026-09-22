import { describe, expect, test } from "bun:test"
import { parseJobCards, parseTotalCount, buildDetail } from "../src/helpers.ts"
import { extractId } from "../src/commands/detail.ts"
import { buildUrl } from "../src/commands/search.ts"

const PAGE = `
<span class="cnt_result">총 2,638건</span>
<div class="item_recruit" value="55089251" data-x="1">
  <div class="area_job">
    <h2 class="job_tit"><a target="_blank" title="[알라딘] 개발2팀 백엔드 엔지니어" href="/zf_user/jobs/relay/view?rec_idx=55089251"><span>[알라딘] 개발2팀 <b>백엔드</b> 엔지니어</span></a></h2>
    <div class="job_date"><span class="date">~ 10/25(일)</span></div>
    <div class="job_condition"><span><a href="#">서울</a> <a href="#">중구</a></span> <span>경력 5~10년</span> <span>초대졸↑</span> <span>정규직</span> <span>4,000 만원</span></div>
    <div class="job_sector"><b><a href="#">백엔드/서버개발</a></b>, <a href="#">Java</a> 외 <span class="job_day">수정일 26/09/21</span></div>
  </div>
  <div class="area_corp"><strong class="corp_name"><a title="(주)알라딘커뮤니케이션" href="#">(주)알라딘커뮤니케이션</a></strong></div>
</div>
<div class="item_recruit" value="55094475">
  <h2 class="job_tit"><a title="두번째" href="#">두번째</a></h2>
  <div class="job_condition"><span>서울전체 , 강남구 , 관악구</span> <span>신입</span> <span>학력무관</span></div>
  <strong class="corp_name"><a title="(주)둘" href="#">(주)둘</a></strong>
</div>
`

describe("parseJobCards", () => {
  test("parses two items", () => {
    const cards = parseJobCards(PAGE)
    expect(cards.length).toBe(2)
    const c = cards[0]!
    expect(c.id).toBe("55089251")
    expect(c.title).toBe("[알라딘] 개발2팀 백엔드 엔지니어")
    expect(c.company).toBe("(주)알라딘커뮤니케이션")
    expect(c.location).toBe("서울 중구")
    expect(c.career).toBe("경력 5~10년")
    expect(c.education).toBe("초대졸↑")
    expect(c.employmentType).toBe("정규직")
    expect(c.salary).toBe("4,000 만원")
    expect(c.sectors).toEqual(["백엔드/서버개발", "Java"])
    expect(c.date).toBe("수정일 26/09/21")
    expect(c.due).toBe("~ 10/25(일)")
    expect(c.url).toBe("https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=55089251")
    const d = cards[1]!
    expect(d.location).toBe("서울전체, 강남구, 관악구")
    expect(d.career).toBe("신입")
    expect(d.education).toBe("학력무관")
    expect(d.employmentType).toBeNull()
  })
  test("total count", () => {
    expect(parseTotalCount(PAGE)).toBe(2638)
    expect(parseTotalCount("")).toBeNull()
  })
})

describe("buildDetail", () => {
  const VIEW = `<meta property="og:title" content="[(주)알라딘커뮤니케이션] [알라딘] 개발2팀 백엔드 엔지니어(D-33) - 사람인">
<meta property="og:description" content="(주)알라딘커뮤니케이션, [알라딘] 개발2팀 백엔드 엔지니어, 경력:경력 5~10년, 학력:대학졸업(2,3년)이상, 면접 후 결정, 마감일:2026-10-25, 홈페이지:www.aladin.co.kr">`
  test("reads og meta and body", () => {
    const d = buildDetail("55089251", VIEW, "<div>채용공고 상세<p>주요업무</p><ul><li>API 개발</li></ul></div>")
    expect(d).not.toBeNull()
    expect(d!.title).toBe("[알라딘] 개발2팀 백엔드 엔지니어")
    expect(d!.company).toBe("(주)알라딘커뮤니케이션")
    expect(d!.career).toBe("경력 5~10년")
    expect(d!.education).toBe("대학졸업(2,3년)이상")
    expect(d!.due).toBe("2026-10-25")
    expect(d!.body).toContain("주요업무")
    expect(d!.body!.startsWith("채용공고 상세")).toBe(false)
  })
  test("no og:title → null", () => {
    expect(buildDetail("1", "<html></html>", null)).toBeNull()
  })
})

describe("cli helpers", () => {
  test("extractId", () => {
    expect(extractId("55089251")).toBe("55089251")
    expect(extractId("https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=55089251&view_type=search")).toBe("55089251")
    expect(extractId("https://www.saramin.co.kr/")).toBeNull()
  })
  test("buildUrl sets filters", () => {
    const u = buildUrl({ query: "백엔드", expCd: "1,2", expMax: 3, loc: "101000", cat: "84", sort: "reg_dt", page: 2, pageSize: 50, format: "json" })
    expect(u).toContain("searchword=%EB%B0%B1%EC%97%94%EB%93%9C")
    expect(u).toContain("exp_cd=1%2C2")
    expect(u).toContain("exp_max=3")
    expect(u).toContain("loc_mcd=101000")
    expect(u).toContain("cat_kewd=84")
    expect(u).toContain("recruitSort=reg_dt")
    expect(u).toContain("recruitPage=2")
    expect(u).toContain("recruitPageCount=50")
  })
})
