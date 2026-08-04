import { ReactNode } from "react";

// Agents reply in markdown. This renders the small subset they actually
// produce (bold, emphasis, inline code, fences, lists, headings) and leaves
// anything it does not recognize as the text it was, which is also what a
// half-streamed chunk looks like until its closing marker arrives.

// Emphasis requires a flanking boundary so dimensions ("a 4*4 grid of 3*3
// bays") stay literal.
const INLINE =
  /(\*\*[^\n]+?\*\*|`[^`\n]+`|\[[^\]\n]+\]\([^)\s]+\)|(?<=^|[\s(])\*[^\s*][^*\n]*\*(?=$|[\s).,;:!?]))/;

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  let rest = text;
  let key = 0;
  while (rest) {
    const match = rest.match(INLINE);
    if (!match || match.index === undefined) {
      out.push(rest);
      break;
    }
    if (match.index > 0) out.push(rest.slice(0, match.index));
    const token = match[0];
    if (token.startsWith("**")) {
      out.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`")) {
      out.push(<code key={key++}>{token.slice(1, -1)}</code>);
    } else if (token.startsWith("[")) {
      // The app promises no URLs, so a link degrades to its label.
      out.push(token.slice(1, token.indexOf("]")));
    } else {
      out.push(<em key={key++}>{token.slice(1, -1)}</em>);
    }
    rest = rest.slice(match.index + token.length);
  }
  return out;
}

const BULLET = /^\s*[-*]\s+/;
const ORDERED = /^\s*\d+[.)]\s+/;
const HEADING = /^\s*#{1,4}\s+/;

function blocks(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const lines = text.split("\n");
  let i = 0;
  let key = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim() === "") {
      i++;
      continue;
    }
    if (line.trimStart().startsWith("```")) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trimStart().startsWith("```")) {
        code.push(lines[i++]);
      }
      i++;
      out.push(
        <pre key={key++}>
          <code>{code.join("\n")}</code>
        </pre>,
      );
      continue;
    }
    if (BULLET.test(line) || ORDERED.test(line)) {
      const marker = BULLET.test(line) ? BULLET : ORDERED;
      const items: ReactNode[] = [];
      while (i < lines.length && marker.test(lines[i])) {
        items.push(<li key={items.length}>{inline(lines[i].replace(marker, ""))}</li>);
        i++;
      }
      out.push(
        marker === BULLET ? <ul key={key++}>{items}</ul> : <ol key={key++}>{items}</ol>,
      );
      continue;
    }
    if (HEADING.test(line)) {
      // A real <h1> is shouting in a chat bubble; a bold line reads right.
      out.push(
        <p key={key++} className="md-heading">
          {inline(line.replace(HEADING, ""))}
        </p>,
      );
      i++;
      continue;
    }
    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].trimStart().startsWith("```") &&
      !BULLET.test(lines[i]) &&
      !ORDERED.test(lines[i]) &&
      !HEADING.test(lines[i])
    ) {
      para.push(lines[i]);
      i++;
    }
    out.push(
      <p key={key++}>
        {para.flatMap((text, n) =>
          n ? [<br key={`br${n}`} />, ...inline(text)] : inline(text),
        )}
      </p>,
    );
  }
  return out;
}

function Markdown({ text }: { text: string }) {
  return <>{blocks(text)}</>;
}

export default Markdown;
