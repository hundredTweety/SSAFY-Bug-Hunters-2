"""Server-side textual patch checker. NEVER eval/exec student submissions."""
import io
import tokenize

def tokens(line):
    # Token check handles irrelevant spacing but intentionally not arbitrary equivalent solutions.
    if not line or '\n' in line or '\r' in line or len(line) > 300:
        return None
    try:
        return tuple((tok.type,tok.string) for tok in tokenize.generate_tokens(io.StringIO(line.strip()).readline)
                     if tok.type not in (tokenize.ENDMARKER,tokenize.NEWLINE,tokenize.NL,
                                         tokenize.INDENT,tokenize.DEDENT,tokenize.COMMENT))
    except (tokenize.TokenError,IndentationError):
        return None

def target_line(question):
    lines=question.buggy_code.splitlines()
    hits=[i+1 for i,s in enumerate(lines) if s.strip()==question.original_line.strip()]
    if len(hits)!=1:
        raise ValueError(f'{question.code}: original line must occur exactly once')
    return hits[0]

def check_patch(question, line_number, user_patch):
    if line_number != target_line(question):
        return False
    proposed = tokens(user_patch)
    return proposed is not None and any(proposed == tokens(accepted) for accepted in question.accepted_patches)
