import json

def _authors_list(authors_json: str | None) -> list[str]:
    if not authors_json:
        return []
    try:
        authors = json.loads(authors_json)
        if isinstance(authors, list):
            return [str(a) for a in authors]
        return [str(authors)]
    except Exception:
        return [authors_json]

def _last_names(authors: list[str]) -> list[str]:
    last_names = []
    for a in authors:
        a_clean = a.strip()
        if a_clean:
            parts = a_clean.split()
            if parts:
                last_names.append(parts[-1])
    return last_names

def _format_author_apa(a: str) -> str:
    parts = a.strip().split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    last = parts[-1]
    # Extract first letter of each part except the last one
    initials = " ".join(f"{p[0]}." for p in parts[:-1] if p)
    return f"{last}, {initials}"

def format_full_citation(paper, style: str) -> str:
    authors = _authors_list(paper.authors)
    year = paper.year or "n.d."
    title = paper.title or "Untitled"
    venue = paper.venue or "Unknown venue"
    style = style.lower()

    if style == "apa":
        if authors:
            formatted = ", ".join(_format_author_apa(a) for a in authors if a.strip())
        else:
            formatted = "Unknown author"
        return f"{formatted} ({year}). {title}. {venue}."
        
    if style == "mla":
        if not authors:
            formatted = "Unknown author"
        else:
            first = authors[0]
            suffix = ", et al." if len(authors) > 1 else ""
            formatted = f"{first}{suffix}"
        return f'{formatted}. "{title}." {venue}, {year}.'
        
    if style == "chicago":
        formatted = ", ".join(authors) if authors else "Unknown author"
        return f'{formatted}. "{title}." {venue} ({year}).'
        
    if style == "ieee":
        formatted = ", ".join(authors) if authors else "Unknown author"
        return f'{formatted}, "{title}," {venue}, {year}.'
        
    return title

def format_in_text(paper, style: str, page: int) -> str:
    last = _last_names(_authors_list(paper.authors))
    year = paper.year or "n.d."
    style = style.lower()
    
    if style == "apa":
        if not last:
            who = "Unknown"
        elif len(last) == 1:
            who = last[0]
        elif len(last) == 2:
            who = f"{last[0]} & {last[1]}"
        else:
            who = f"{last[0]} et al."
        return f"({who}, {year}, p. {page})"
        
    if style == "mla":
        who = last[0] if last else "Unknown"
        return f"({who} {page})"
        
    if style == "chicago":
        who = last[0] if last else "Unknown"
        return f"({who} {year}, {page})"
        
    if style == "ieee":
        return f"[1, p. {page}]"
        
    return f"(p. {page})"
