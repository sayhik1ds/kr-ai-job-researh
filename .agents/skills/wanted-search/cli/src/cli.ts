#!/usr/bin/env bun
import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"
import { writeError } from "./helpers.js"

const USAGE = `wanted-cli — search jobs on Wanted (wanted.co.kr), Korea's startup job portal

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <id|url> [--format json|plain]

SEARCH FLAGS
  --query, -q <text>      Keyword (job title, skill, stack). Uses Wanted's search
                          endpoint. Without it, the category browse endpoint is
                          used and --job-group/--job-ids apply instead.
  --job-group <id>        Wanted job-group id. 518 = 개발. Ignored when --query is set.
  --job-ids <id[,id...]>  Job-category ids, repeatable or comma-separated.
                          660 = 서버/백엔드 개발자, 872 = 웹 개발자, 873 = 소프트웨어 엔지니어.
  --years-min <n>         Minimum years of experience. 0 = 신입.
  --years-max <n>         Maximum years of experience.
  --location <text>       Location filter. Default "all". e.g. "seoul.all".
  --page <n>              1-indexed page (20 results/page). Default 1.
  --limit, -n <n>         Cap results emitted (client-side).
  --format <fmt>          json (default) | table | plain.

EXAMPLES
  bun run src/cli.ts search -q "백엔드 개발자" --limit 5 --format table
  bun run src/cli.ts search -q "Spring Boot" --years-min 0 --years-max 3 --format table
  bun run src/cli.ts search --job-group 518 --job-ids 660,872,873 --years-min 0 --years-max 3 -n 10 --format table
  bun run src/cli.ts detail 384433 --format plain
  bun run src/cli.ts detail https://www.wanted.co.kr/wd/384433

Personal use only — uses Wanted's public web API; keep volume low.
`

function parseIntFlag(raw: string | undefined, name: string): number {
  const n = Number(raw)
  if (!Number.isInteger(n)) throw new Error(`${name} expects an integer, got: ${raw}`)
  return n
}

function main(argv: string[]): Promise<number> | number {
  const [command, ...rest] = argv
  if (command === undefined || command === "--help" || command === "-h" || command === "help") {
    process.stdout.write(USAGE)
    return 0
  }

  if (command === "search") {
    const opts: SearchOpts = {
      jobIds: [],
      yearsMin: -1,
      yearsMax: -1,
      location: "all",
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
        case "--job-group":
          opts.jobGroup = parseIntFlag(value, flag)
          i++
          break
        case "--job-ids":
          if (value === undefined) throw new Error("--job-ids expects a value")
          for (const part of value.split(",")) {
            const n = Number(part.trim())
            if (!Number.isInteger(n)) throw new Error(`--job-ids expects integers, got: ${part}`)
            opts.jobIds.push(n)
          }
          i++
          break
        case "--years-min":
          opts.yearsMin = parseIntFlag(value, flag)
          i++
          break
        case "--years-max":
          opts.yearsMax = parseIntFlag(value, flag)
          i++
          break
        case "--location":
          if (value === undefined) throw new Error("--location expects a value")
          opts.location = value
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
    if (!opts.query && opts.jobGroup === undefined && opts.jobIds.length === 0) {
      throw new Error("Provide --query, or --job-group/--job-ids for a category browse.")
    }
    return runSearch(opts)
  }

  if (command === "detail") {
    const idOrUrl = rest[0]
    if (idOrUrl === undefined || idOrUrl.startsWith("-")) {
      throw new Error("detail expects a job id or URL as its first argument")
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
