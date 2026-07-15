package cmd

import (
	"bufio"
	"bytes"
	"fmt"
	"os/exec"
	"strings"
)

func search(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi search <query>")
	}

	if isWindows() {
		return searchWinget(args[0])
	}

	return runPacman(append([]string{"-Ss"}, args...)...)
}

func searchWinget(query string) error {
	c := exec.Command("winget", "search", query)
	var outBuf, errBuf bytes.Buffer
	c.Stdout = &outBuf
	c.Stderr = &errBuf

	err := c.Run()

	sc := bufio.NewScanner(strings.NewReader(outBuf.String()))
	for sc.Scan() {
		line := sc.Text()
		lower := strings.ToLower(line)
		if strings.Contains(lower, "microsoft") || strings.Contains(lower, "license") {
			continue
		}
		if strings.TrimSpace(line) == "" || strings.HasPrefix(line, "---") {
			continue
		}
		line = strings.ReplaceAll(line, "winget", "mochi")
		line = strings.ReplaceAll(line, "msstore", "mochi")
		fmt.Println(line)
	}

	if err != nil && errBuf.Len() > 0 {
		return fmt.Errorf("search failed: %s", errBuf.String())
	}
	return nil
}
