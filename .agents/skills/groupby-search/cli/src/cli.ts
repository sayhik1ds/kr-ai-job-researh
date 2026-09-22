#!/usr/bin/env bun
import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"
import { writeError } from "./helpers.js"

const USAGE = `groupby-cli — browse GroupBy (groupby.kr), Korean startup job postings

USAGE
  bun run src/cli.ts search [flags]
  bun run src/cli.ts detail <id|url> [--format json|plain]

SEARCH FLAGS
  --query, -q <text>   Filter the fetched feed by title, company, role or stack.
                       Client-side: GroupBy exposes no server-side search to
                       anonymous callers.
  --limit, -n <n>      Cap results emitted.
  --format <fmt>       json (default) | table | plain.

SCOPE
  The site server-renders only the newest page of its listing (10 postings) and
  ignores limit/offset in the URL, so \`search\` sees that page and nothing more.
  \`detail\` works for any posting id. Treat \`search\` as a "what is new on
  GroupBy" probe, not a portal-wide sweep.

EXAMPLES
  bun run src/cli.ts search --format table
  bun run src/cli.ts search -q "백엔드" --format json
  bun run src/cli.ts detail 12218 --format plain
  bun run src/cli.ts detail https://groupby.kr/positions/12218

Personal use only — reads GroupBy's public pages; keep volume low.
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
    const opts: SearchOpts = { format: "json" }
    for (let i = 0; i < rest.length; i++) {
      const flag = rest[i]!
      const value = rest[i + 1]
      switch (flag) {
        case "--query":
        case "-q":
          opts.query = value
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
