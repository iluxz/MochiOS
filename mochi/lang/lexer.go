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
		tokens = append(tokens, tok)
		if tok.Type == EOF {
			break
		}
	}
	for len(l.indentStack) > 1 {
		tokens = append(tokens, Token{Type: DEDENT, Line: l.line, Col: l.col})
		l.indentStack = l.indentStack[:len(l.indentStack)-1]
	}
	return tokens
}

func (l *Lexer) nextToken() Token {
	if len(l.pending) > 0 {
		tok := l.pending[0]
		l.pending = l.pending[1:]
		return tok
	}

	l.skipWhitespace()

	if l.pos >= len(l.input) {
		return Token{Type: EOF, Literal: "", Line: l.line, Col: l.col}
	}

	ch := l.input[l.pos]

	if l.atLineStart {
		l.atLineStart = false
		indent := l.countIndent()
		last := l.indentStack[len(l.indentStack)-1]
		if ch == '#' || ch == '\n' || l.pos >= len(l.input) {
			l.skipLine()
			return l.nextToken()
		}
		if indent > last {
			l.indentStack = append(l.indentStack, indent)
			return Token{Type: INDENT, Literal: "", Line: l.line, Col: l.col}
		} else if indent < last {
			for len(l.indentStack) > 1 && l.indentStack[len(l.indentStack)-1] != indent {
				l.indentStack = l.indentStack[:len(l.indentStack)-1]
				l.pending = append(l.pending, Token{Type: DEDENT, Line: l.line, Col: l.col})
			}
			if len(l.indentStack) > 1 && l.indentStack[len(l.indentStack)-1] > indent {
				l.indentStack = l.indentStack[:len(l.indentStack)-1]
				l.pending = append(l.pending, Token{Type: DEDENT, Line: l.line, Col: l.col})
			}
			return l.nextToken()
		}
	}

	switch {
	case ch == '\n':
		l.pos++
		l.line++
		l.col = 0
		l.atLineStart = true
		return Token{Type: NEWLINE, Literal: "\\n", Line: l.line - 1, Col: l.col}

	case ch == '#':
		l.skipLine()
		return l.nextToken()

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

func (l *Lexer) skipWhitespace() {
	for l.pos < len(l.input) {
		ch := l.input[l.pos]
		if ch == ' ' || ch == '\t' || ch == '\r' {
			l.pos++
			l.col++
		} else {
			break
		}
	}
}

func (l *Lexer) skipLine() {
	for l.pos < len(l.input) && l.input[l.pos] != '\n' {
		l.pos++
	}
}

func (l *Lexer) countIndent() int {
	pos := l.pos
	count := 0
	for pos < len(l.input) {
		ch := l.input[pos]
		if ch == ' ' {
			count++
			pos++
		} else if ch == '\t' {
			count += 4
			pos++
		} else {
			break
		}
	}
	return count
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
	hasDot := false
	for l.pos < len(l.input) {
		ch := l.input[l.pos]
		if ch == '.' && !hasDot {
			hasDot = true
			l.pos++
			l.col++
		} else if unicode.IsDigit(ch) {
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
