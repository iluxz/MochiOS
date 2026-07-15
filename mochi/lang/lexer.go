package lang

import (
	"unicode"
)

type Lexer struct {
	input        []rune
	pos          int
	line         int
	col          int
	indentStack  []int
	pending      []Token
	atLineStart  bool
}

func Lex(input string) []Token {
	l := &Lexer{
		input:       []rune(input),
		line:        1,
		col:         0,
		indentStack: []int{0},
		atLineStart: true,
	}
	var tokens []Token
	for {
		tok := l.nextToken()
		if tok.Type == EOF {
			for len(l.indentStack) > 1 {
				l.indentStack = l.indentStack[:len(l.indentStack)-1]
				tokens = append(tokens, Token{Type: DEDENT, Line: l.line, Col: l.col})
			}
			tokens = append(tokens, tok)
			break
		}
		tokens = append(tokens, tok)
	}
	return tokens
}

func (l *Lexer) nextToken() Token {
	if len(l.pending) > 0 {
		tok := l.pending[0]
		l.pending = l.pending[1:]
		return tok
	}

	if l.atLineStart {
		l.atLineStart = false
		indent := l.countAndSkipIndent()
		last := l.indentStack[len(l.indentStack)-1]

		if l.pos >= len(l.input) {
			if indent < last {
				return l.emitDedent()
			}
			return Token{Type: EOF, Line: l.line, Col: l.col}
		}

		ch := l.input[l.pos]
		if ch == '#' {
			l.skipLine()
			l.atLineStart = true
			return l.nextToken()
		}
		if ch == '\n' {
			l.pos++
			l.line++
			l.col = 0
			l.atLineStart = true
			return Token{Type: NEWLINE, Literal: "\\n", Line: l.line - 1, Col: l.col}
		}

		if indent > last {
			l.indentStack = append(l.indentStack, indent)
			return Token{Type: INDENT, Line: l.line, Col: l.col}
		}
		if indent < last {
			return l.emitDedent()
		}
	} else {
		l.skipInlineSpace()
	}

	if l.pos >= len(l.input) {
		return Token{Type: EOF, Line: l.line, Col: l.col}
	}

	ch := l.input[l.pos]

	switch {
	case ch == '\n':
		l.pos++
		l.line++
		l.col = 0
		l.atLineStart = true
		return Token{Type: NEWLINE, Literal: "\\n", Line: l.line - 1, Col: l.col}

	case ch == '=':
		l.pos++
		l.col++
		return Token{Type: ASSIGN, Literal: "=", Line: l.line, Col: l.col - 1}

	case ch == '+':
		l.pos++
		l.col++
		return Token{Type: PLUS, Literal: "+", Line: l.line, Col: l.col - 1}

	case ch == '-':
		l.pos++
		l.col++
		return Token{Type: MINUS, Literal: "-", Line: l.line, Col: l.col - 1}

	case ch == '*':
		l.pos++
		l.col++
		return Token{Type: STAR, Literal: "*", Line: l.line, Col: l.col - 1}

	case ch == '/':
		l.pos++
		l.col++
		return Token{Type: SLASH, Literal: "/", Line: l.line, Col: l.col - 1}

	case ch == '!':
		if l.pos+1 < len(l.input) && l.input[l.pos+1] == '=' {
			l.pos += 2
			l.col += 2
			return Token{Type: NEQ, Literal: "!=", Line: l.line, Col: l.col - 2}
		}
		return Token{Type: ILLEGAL, Literal: "!", Line: l.line, Col: l.col}

	case ch == '<':
		l.pos++
		l.col++
		if l.pos < len(l.input) && l.input[l.pos] == '=' {
			l.pos++
			l.col++
			return Token{Type: LE, Literal: "<=", Line: l.line, Col: l.col - 2}
		}
		return Token{Type: LT, Literal: "<", Line: l.line, Col: l.col - 1}

	case ch == '>':
		l.pos++
		l.col++
		if l.pos < len(l.input) && l.input[l.pos] == '=' {
			l.pos++
			l.col++
			return Token{Type: GE, Literal: ">=", Line: l.line, Col: l.col - 2}
		}
		return Token{Type: GT, Literal: ">", Line: l.line, Col: l.col - 1}

	case ch == ',':
		l.pos++
		l.col++
		return Token{Type: COMMA, Literal: ",", Line: l.line, Col: l.col - 1}

	case ch == '(':
		l.pos++
		l.col++
		return Token{Type: LPAREN, Literal: "(", Line: l.line, Col: l.col - 1}

	case ch == ')':
		l.pos++
		l.col++
		return Token{Type: RPAREN, Literal: ")", Line: l.line, Col: l.col - 1}

	case ch == '[':
		l.pos++
		l.col++
		return Token{Type: LBRACKET, Literal: "[", Line: l.line, Col: l.col - 1}

	case ch == ']':
		l.pos++
		l.col++
		return Token{Type: RBRACKET, Literal: "]", Line: l.line, Col: l.col - 1}

	case ch == '"' || ch == '\'':
		return l.readString(ch)

	case unicode.IsDigit(ch):
		return l.readNumber()

	case unicode.IsLetter(ch) || ch == '_':
		return l.readIdent()

	default:
		l.pos++
		l.col++
		return Token{Type: ILLEGAL, Literal: string(ch), Line: l.line, Col: l.col - 1}
	}
}

func (l *Lexer) emitDedent() Token {
	for len(l.indentStack) > 1 {
		l.indentStack = l.indentStack[:len(l.indentStack)-1]
		l.pending = append(l.pending, Token{Type: DEDENT, Line: l.line, Col: l.col})
	}
	if len(l.pending) > 0 {
		tok := l.pending[0]
		l.pending = l.pending[1:]
		return tok
	}
	return Token{Type: DEDENT, Line: l.line, Col: l.col}
}

func (l *Lexer) countAndSkipIndent() int {
	count := 0
	for l.pos < len(l.input) {
		ch := l.input[l.pos]
		if ch == ' ' {
			count++
			l.pos++
		} else if ch == '\t' {
			count += 4
			l.pos++
		} else {
			break
		}
	}
	return count
}

func (l *Lexer) skipInlineSpace() {
	for l.pos < len(l.input) && (l.input[l.pos] == ' ' || l.input[l.pos] == '\t') {
		l.pos++
		l.col++
	}
}

func (l *Lexer) skipLine() {
	for l.pos < len(l.input) && l.input[l.pos] != '\n' {
		l.pos++
	}
}

func (l *Lexer) readString(quote rune) Token {
	start := l.pos
	l.pos++
	l.col++
	for l.pos < len(l.input) && l.input[l.pos] != quote {
		if l.input[l.pos] == '\n' {
			l.line++
			l.col = 0
		} else {
			l.col++
		}
		l.pos++
	}
	if l.pos < len(l.input) {
		l.pos++
		l.col++
	}
	return Token{
		Type:    STRING,
		Literal: string(l.input[start+1 : l.pos-1]),
		Line:    l.line,
		Col:     l.col - len(string(l.input[start:l.pos])),
	}
}

func (l *Lexer) readNumber() Token {
	start := l.pos
	for l.pos < len(l.input) {
		ch := l.input[l.pos]
		if unicode.IsDigit(ch) || ch == '.' {
			l.pos++
			l.col++
		} else {
			break
		}
	}
	return Token{
		Type:    NUMBER,
		Literal: string(l.input[start:l.pos]),
		Line:    l.line,
		Col:     l.col - (l.pos - start),
	}
}

func (l *Lexer) readIdent() Token {
	start := l.pos
	for l.pos < len(l.input) {
		ch := l.input[l.pos]
		if unicode.IsLetter(ch) || unicode.IsDigit(ch) || ch == '_' {
			l.pos++
			l.col++
		} else {
			break
		}
	}
	lit := string(l.input[start:l.pos])
	return Token{
		Type:    LookupIdent(lit),
		Literal: lit,
		Line:    l.line,
		Col:     l.col - (l.pos - start),
	}
}
