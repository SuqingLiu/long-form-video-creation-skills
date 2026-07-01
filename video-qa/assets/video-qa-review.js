export const meta = {
  name: 'video-qa-review',
  description: 'Parallel per-segment QA review of a rendered video: detect text overlaps, off-screen elements, persistent clipping, spacing collisions, and low-contrast text from sampled frames — using persistence filtering to reject animation transients.',
  phases: [
    { title: 'Review', detail: 'one reviewer agent per time segment' },
  ],
}

// ---- args ------------------------------------------------------------------
// dir        : absolute path to the frames directory (t####.png files)
// maxSec     : last sampled second (from extract_qa_frames.sh MAXSEC)
// step       : sampling step in seconds (must match extraction; default 2)
// segmentSec : seconds of video per reviewer agent (default 60 = one per minute)
// context    : optional one-line description of the video's visual style
const DIR = args.dir
const MAX = args.maxSec
const STEP = args.step || 2
const SEG = args.segmentSec || 60
const CONTEXT = args.context ||
  'a rendered explainer video (likely dark theme, 16:9, with burned-in subtitles at the bottom)'

const ISSUE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    segment: { type: 'string' },
    framesReviewed: { type: 'integer' },
    verdict: { type: 'string', enum: ['clean', 'issues_found'] },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        properties: {
          timestamps: { type: 'string', description: 'e.g. "t0090,t0092" — which frames show it' },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          type: { type: 'string', enum: ['overlap', 'offscreen', 'clipping', 'spacing', 'contrast', 'other'] },
          persistent: { type: 'boolean', description: 'true if confirmed across >=2 consecutive frames' },
          description: { type: 'string', description: 'what and where, precisely' },
        },
        required: ['timestamps', 'severity', 'type', 'persistent', 'description'],
      },
    },
  },
  required: ['segment', 'framesReviewed', 'verdict', 'issues'],
}

const pad = (n) => String(n).padStart(4, '0')
const fmt = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

// build segments, each listing the exact frame paths it owns
const segments = []
for (let start = 0; start <= MAX; start += SEG) {
  const end = start + SEG
  const frames = []
  for (let s = start; s < end && s <= MAX; s += STEP) {
    frames.push(`${DIR}/t${pad(s)}.png`)
  }
  if (frames.length) {
    segments.push({ label: `${fmt(start)}-${fmt(Math.min(end, MAX + 1) - 1)}`, frames })
  }
}

log(`Reviewing ${segments.length} segments (${SEG}s each) in parallel`)

const prompt = (seg) => `You are QA-reviewing one segment of ${CONTEXT}. Your ONLY job is to find VISUAL LAYOUT DEFECTS in the text and graphics.

This segment covers ${seg.label}. Below are ${seg.frames.length} frames sampled every ${STEP} seconds. READ EVERY ONE with the Read tool (they are PNG images), in order:
${seg.frames.map((f) => `- ${f}`).join('\n')}

For each frame, look for:
1. overlap — text overlapping other text, or text overlapping a shape/figure so either becomes hard to read
2. offscreen — any text or element running off the top/bottom/left/right edge of the frame
3. clipping — text that is persistently garbled, cut off, or truncated
4. spacing — elements colliding or awkwardly cramped (e.g. a label touching a bar, two rows too close, collapsed word spacing on small text)
5. contrast — text/shape too dark or low-contrast to read against the background

CRITICAL — reject animation transients. Frames are ${STEP} seconds apart. Animations (fades, writes, transforms, growing arrows, flashes) are in progress in some frames. Text that looks half-drawn / partially rendered / clipped in only ONE frame but looks fine in the neighboring frames is a mid-animation snapshot and is NOT a defect — DO NOT report it. Only report a defect if:
  - it PERSISTS across >=2 consecutive frames (set persistent=true), OR
  - it is an unambiguous static layout error like text clearly off the frame edge or a hard overlap that cannot be a transition.
When unsure, prefer NOT reporting — false positives are worse than misses here. Note: a bottom subtitle sitting over its own semi-transparent dark bar is by design, not an overlap. The MOST COMMON real defect is a bottom subtitle overlapping other on-screen content that sits too low — check for that specifically.

Set verdict='clean' with an empty issues array if you find nothing solid. Otherwise list each distinct defect once (cite the timestamps where you saw it). Return only the structured object.`

const results = await parallel(
  segments.map((seg) => () =>
    agent(prompt(seg), {
      label: `qa:${seg.label}`,
      phase: 'Review',
      schema: ISSUE_SCHEMA,
    })
  )
)

const reviewed = results.filter(Boolean)
const allIssues = reviewed.flatMap((s) => (s.issues || []).map((i) => ({ ...i, segment: s.segment })))
const persistent = allIssues.filter((i) => i.persistent || i.type === 'offscreen')
const bySev = (s) => allIssues.filter((i) => i.severity === s).length
log(`Done: ${reviewed.length} segments, ${allIssues.length} issues ` +
    `(high ${bySev('high')}, medium ${bySev('medium')}, low ${bySev('low')}); ` +
    `${persistent.length} persistent/hard`)

return { segments: reviewed, allIssues, persistent }
