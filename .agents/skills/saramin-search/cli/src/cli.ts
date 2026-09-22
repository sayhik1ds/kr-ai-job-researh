#!/usr/bin/env bun
import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"
import { writeError, EXP_CD, LOC_MCD, CAT_KEWD } from "./helpers.js"

const USAGE = `saramin-cli — search jobs on Saramin (saramin.co.kr), Korea's largest general job portal

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <rec_idx|url> [--format json|plain]

SEARCH FLAGS
  --query, -q <text>        Keyword (server-side full-text search). Recommended.
  --exp <codes>             exp_cd, comma-joined. ${Object.entries(EXP_CD).map(([k, v]) => `${k} = ${v}`).join(", ")}
  --exp-min <n>             Minimum years of experience (exp_min).
  --exp-max <n>             Maximum years of experience (exp_max).
  --loc <codes>             loc_mcd, comma-joined. ${Object.entries(LOC_MCD).map(([k, v]) => `${k} = ${v}`).join(", ")}
  --cat <codes>             cat_kewd, comma-joined. ${Object.entries(CAT_KEWD).map(([k, v]) => `${k} = ${v}`).join(", ")}
  --sort <key>              recruitSort. relation (default) | reg_dt (최신).
  --page <n>                1-indexed page. Default 1.
  --page-size <n>           Results per page. Default 20, max 100.
  --limit, -n <n>           Cap results emitted (client-side).
  --format <fmt>            json (default) | table | plain.

EXAMPLES
  bun run src/cli.ts search -q "백엔드" --exp 1,2 --exp-max 3 --loc 101000 --limit 10 --format table
  bun run src/cli.ts search -q "Spring Boot" --sort reg_dt --format json
  bun run src/cli.ts detail 55089251 --format plain
  bun run src/cli.ts detail "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=55089251"

Personal use only — reads Saramin's public pages; keep volume low. For heavier use,
Saramin's official Open API (oapi.saramin.co.kr) with an access key is the sanctioned route.
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
    const opts: SearchOpts = { sort: "relation", page: 1, pageSize: 20, format: "json" }
    for (let i = 0; i < rest.length; i++) {
      const flag = rest[i]!
      const value = rest[i + 1]
      switch (flag) {
        case "--query":
        case "-q":
          opts.query = need(value, flag)
          i++
          break
        case "--exp":
          opts.expCd = need(value, flag)
          i++
          break
        case "--exp-min":
          opts.expMin = parseIntFlag(value, flag)
          i++
          break
        case "--exp-max":
          opts.expMax = parseIntFlag(value, flag)
          i++
          break
        case "--loc":
          opts.loc = need(value, flag)
          i++
          break
        case "--cat":
          opts.cat = need(value, flag)
          i++
          break
        case "--sort":
          opts.sort = need(value, flag)
          i++
          break
        case "--page":
          opts.page = parseIntFlag(value, flag)
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
    if (opts.pageSize < 1 || opts.pageSize > 100) throw new Error("--page-size must be 1..100")
    return runSearch(opts)
  }

  if (command === "detail") {
    const idOrUrl = rest[0]
    if (idOrUrl === undefined || idOrUrl.startsWith("-")) {
      throw new Error("detail expects a rec_idx or URL as its first argument")
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
