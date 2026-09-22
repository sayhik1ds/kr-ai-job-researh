#!/usr/bin/env bun
import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"
import { writeError } from "./helpers.js"

const USAGE = `jumpit-cli — search jobs on Jumpit (jumpit.saramin.co.kr), Korea's developer job portal

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <id|url> [--format json|plain]

SEARCH FLAGS
  --query, -q <text>        Keyword (job title, stack, company). Recommended.
  --job-category <id[,id]>  Jumpit job-category ids, repeatable or comma-separated.
                            1 = 서버/백엔드 개발자, 2 = 프론트엔드 개발자, 16 = 데이터 엔지니어.
  --tech-stack <id[,id]>    Tech-stack ids, repeatable or comma-separated.
  --career <n>              Minimum years of experience. 0 = 신입.
  --sort <key>              rsp_rate (default, 응답률순) | reg_dt (최신순) | popular.
  --page <n>                1-indexed page (16 results/page). Default 1.
  --limit, -n <n>           Cap results emitted (client-side).
  --format <fmt>            json (default) | table | plain.

EXAMPLES
  bun run src/cli.ts search -q "백엔드" --limit 5 --format table
  bun run src/cli.ts search -q "Spring Boot" --career 0 --sort reg_dt --format table
  bun run src/cli.ts search --job-category 1 -n 20 --format json
  bun run src/cli.ts detail 55030576 --format plain
  bun run src/cli.ts detail https://jumpit.saramin.co.kr/position/55030576

Personal use only — uses Jumpit's public web API; keep volume low.
`

function parseIntFlag(raw: string | undefined, name: string): number {
  const n = Number(raw)
  if (!Number.isInteger(n)) throw new Error(`${name} expects an integer, got: ${raw}`)
  return n
}

function pushIds(target: number[], value: string | undefined, name: string): void {
  if (value === undefined) throw new Error(`${name} expects a value`)
  for (const part of value.split(",")) {
    const n = Number(part.trim())
    if (!Number.isInteger(n)) throw new Error(`${name} expects integers, got: ${part}`)
    target.push(n)
  }
}

function main(argv: string[]): Promise<number> | number {
  const [command, ...rest] = argv
  if (command === undefined || command === "--help" || command === "-h" || command === "help") {
    process.stdout.write(USAGE)
    return 0
  }

  if (command === "search") {
    const opts: SearchOpts = {
      jobCategories: [],
      techStacks: [],
      career: -1,
      sort: "rsp_rate",
      page: 1,
      format: "json",
    }
    for (let i = 0; i < rest.length; i++) {
      const flag = rest[i]!
      const value = rest[i + 1]
      switch (flag) {
        case "--query":
        case "-q":
          opts.query = value
          i++
          break
        case "--job-category":
          pushIds(opts.jobCategories, value, flag)
          i++
          break
        case "--tech-stack":
          pushIds(opts.techStacks, value, flag)
          i++
          break
        case "--career":
          opts.career = parseIntFlag(value, flag)
          i++
          break
        case "--sort":
          if (value === undefined) throw new Error("--sort expects a value")
          opts.sort = value
          i++
          break
        case "--page":
          opts.page = parseIntFlag(value, flag)
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
    return runSearch(opts)
  }

  if (command === "detail") {
    const idOrUrl = rest[0]
    if (idOrUrl === undefined || idOrUrl.startsWith("-")) {
      throw new Error("detail expects a position id or URL as its first argument")
    }
    const opts: DetailOpts = { idOrUrl, format: "json" }
    for (let i = 1; i < rest.length; i++) {
      const flag = rest[i]!
      const value = rest[i + 1]
      if (flag === "--format") {
        if (value !== "json" && value !== "plain") {
          throw new Error(`--format expects json|plain, got: ${value}`)
        }
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
