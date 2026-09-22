#!/usr/bin/env bun
import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"
import { writeError, DUTY_CTGR, LOCAL } from "./helpers.js"

const USAGE = `jobkorea-cli — browse job postings on JobKorea (jobkorea.co.kr) by category, region and career

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <id|url> [--format json|plain]

SEARCH FLAGS
  --query, -q <regex>       Client-side filter over title, summary and company (case-insensitive).
                            JobKorea's keyword search endpoint is disallowed by robots.txt, so
                            keywords never reach the server.
  --duty-ctgr <id>          대분류 category. Default 10031 (AI·개발·데이터).
                            ${Object.entries(DUTY_CTGR).map(([k, v]) => `${k} = ${v}`).join(", ")}
  --duty <codes>            Sub-duty codes, comma-joined (passed through as-is).
  --local <codes>           Region codes, comma-joined. ${Object.entries(LOCAL).map(([k, v]) => `${k} = ${v}`).join(", ")}
  --career-min <n>          Minimum years of experience.
  --career-max <n>          Maximum years of experience.
  --page <n>                1-indexed page. Default 1.
  --pages <n>               Pages to fetch and merge. Default 1. Use 2-5 with -q to widen the net.
  --page-size <n>           Rows per page. Default 40.
  --limit, -n <n>           Cap results emitted (client-side).
  --format <fmt>            json (default) | table | plain.

EXAMPLES
  bun run src/cli.ts search --local I000 --career-min 0 --career-max 3 --limit 20 --format table
  bun run src/cli.ts search -q "백엔드|서버|Spring" --pages 3 --format json
  bun run src/cli.ts detail 50038225 --format plain
  bun run src/cli.ts detail https://www.jobkorea.co.kr/Recruit/GI_Read/50038225

Personal use only — reads JobKorea's public pages; keep volume low.
`

function parseIntFlag(raw: string | undefined, name: string): number {
  const n = Number(raw)
  if (!Number.isInteger(n)) throw new Error(`${name} expects an integer, got: ${raw}`)
  return n
}

function need(value: string | undefined, name: string): string {
  if (value === undefined) throw new Error(`${name} expects a value`)
  return value
}

function main(argv: string[]): Promise<number> | number {
  const [command, ...rest] = argv
  if (command === undefined || command === "--help" || command === "-h" || command === "help") {
    process.stdout.write(USAGE)
    return 0
  }

  if (command === "search") {
    const opts: SearchOpts = { dutyCtgr: "10031", page: 1, pages: 1, pageSize: 40, format: "json" }
    for (let i = 0; i < rest.length; i++) {
      const flag = rest[i]!
      const value = rest[i + 1]
      switch (flag) {
        case "--query":
        case "-q":
          opts.query = need(value, flag)
          i++
          break
        case "--duty-ctgr":
          opts.dutyCtgr = need(value, flag)
          i++
          break
        case "--duty":
          opts.duty = need(value, flag)
          i++
          break
        case "--local":
          opts.local = need(value, flag)
          i++
          break
        case "--career-min":
          opts.careerMin = parseIntFlag(value, flag)
          i++
          break
        case "--career-max":
          opts.careerMax = parseIntFlag(value, flag)
          i++
          break
        case "--page":
          opts.page = parseIntFlag(value, flag)
          i++
          break
        case "--pages":
          opts.pages = parseIntFlag(value, flag)
          i++
          break
        case "--page-size":
          opts.pageSize = parseIntFlag(value, flag)
          i++
          break
        case "--limit":
        case "-n":
          opts.limit = parseIntFlag(value, flag)
          i++
          break
        case "--format":
          if (value !== "json" && value !== "table" && value !== "plain") {
            throw new Error(`--format expects json|table|plain, got: ${value}`)
          }
          opts.format = value
          i++
          break
        default:
          throw new Error(`Unknown flag: ${flag}`)
      }
    }
    if (opts.page < 1) throw new Error("--page must be >= 1")
    if (opts.pages < 1 || opts.pages > 10) throw new Error("--pages must be 1..10")
    return runSearch(opts)
  }

  if (command === "detail") {
    const idOrUrl = rest[0]
    if (idOrUrl === undefined || idOrUrl.startsWith("-")) {
      throw new Error("detail expects a posting id or URL as its first argument")
    }
    const opts: DetailOpts = { idOrUrl, format: "json" }
    for (let i = 1; i < rest.length; i++) {
      const flag = rest[i]!
      const value = rest[i + 1]
      if (flag === "--format") {
        if (value !== "json" && value !== "plain") throw new Error(`--format expects json|plain, got: ${value}`)
        opts.format = value
        i++
      } else {
        throw new Error(`Unknown flag: ${flag}`)
      }
    }
    return runDetail(opts)
  }

  throw new Error(`Unknown command: ${command}. Run with --help for usage.`)
}

try {
  const result = main(process.argv.slice(2))
  process.exit(result instanceof Promise ? await result : result)
} catch (e) {
  writeError(e instanceof Error ? e.message : String(e), "BAD_INVOCATION")
  process.exit(2)
}
