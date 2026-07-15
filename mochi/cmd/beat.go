package cmd

import (
	"bufio"
	"bytes"
	"fmt"
	"os/exec"
	"strings"
)

func beat(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi beat <package>...")
	}

	if isWindows() {
		for _, pkg := range args {
			fmt.Printf("beating %s... ", pkg)
			err := beatWinget(pkg)
			if err != nil {
				fmt.Println("failed")
				return err
			}
			fmt.Println("done!")
		}
		return nil
	}

	for _, pkg := range args {
		fmt.Printf("beating %s...\n", pkg)
	}
	return runPacman(append([]string{"-S", "--needed"}, args...)...)
}

func beatWinget(pkg string) error {
	// Resolve short name to exact ID via search, then install by ID
	id, err := resolvePackage(pkg)
	if err != nil {
		// Maybe it's an ID already — try direct
		return runWinget("install", "--id", "--exact", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements", pkg)
	}

	return runWinget("install", "--id", "--exact", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements", id)
}

func resolvePackage(query string) (string, error) {
	c := exec.Command("winget", "search", "--accept-source-agreements", query)
	var outBuf bytes.Buffer
	c.Stdout = &outBuf

	if err := c.Run(); err != nil {
		return "", fmt.Errorf("no package found matching '%s'", query)
	}

	sc := bufio.NewScanner(strings.NewReader(outBuf.String()))
	var ids []string
	for sc.Scan() {
		line := sc.Text()
		if len(line) < 10 || strings.Contains(line, "---") || strings.Contains(line, "Name ") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) < 3 {
			continue
		}
		source := strings.ToLower(parts[len(parts)-1])
		if source != "winget" && source != "mochi" {
			continue
		}
		ids = append(ids, parts[len(parts)-2])
	}

	if len(ids) == 0 {
		return "", fmt.Errorf("no package found matching '%s'", query)
	}

	return pickBest(ids, query), nil
}

func pickBest(ids []string, query string) string {
	// If any ID matches the query exactly, use it
	for _, id := range ids {
		if strings.EqualFold(id, query) {
			return id
		}
	}

	// Prefer non-locale variant (no .locale suffix like .en-us or .MSIX)
	for _, id := range ids {
		namePart := id
		if idx := strings.Index(id, "."); idx != -1 {
			namePart = id[:idx]
		}
		check := strings.ToLower(id)
		if !strings.Contains(check, "."+strings.ToLower(namePart)) && !strings.HasSuffix(check, ".msix") {
			return id
		}
	}

	// Fallback: first ID
	return ids[0]
}
